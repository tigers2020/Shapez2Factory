import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.db.models import Prefetch
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from django_apps.asteroid_lab.models import (
    AsteroidMapInput,
    AsteroidProject,
    ReplayFrame,
    ReplayTrack,
)
from django_apps.asteroid_lab.services.input_service import (
    content_sha256_for_copy_code,
    create_copy_code_map_input,
)
from django_apps.asteroid_lab.services.project_service import (
    resolve_or_create_project_slug_for_copy_code,
)
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)
from django_apps.shapez_core.services.preview_service import (
    build_demo_parse_rows,
    get_color_catalog_rows,
    get_shape_catalog_rows,
)
from django_apps.shapez_solver.services.pattern_lab_service import analyze_pattern_lab_shape
from django_apps.web.constants import (
    DEMO_FIXED_SAMPLE_CODES,
    HOME_INITIAL_SHAPE_CODE,
)
from django_apps.web.models import GraphPreviewImage
from django_apps.web.services.asteroid_lab_optimization_run import (
    run_lab_solver_optimization_for_map_input,
)
from django_apps.web.services.asteroid_lab_page_context import (
    build_lab_replay_payload,
    inspection_replay_track_for_map_input,
    lab_page_context,
    serialize_replay_frame,
)
from django_apps.web.services.graph_preview import (
    PlaywrightPngGraphPreviewRenderer,
    png_bytes_are_valid,
)
from django_apps.web.services.replay_frame_cell_lookup import lookup_cell_in_serialized_frame


@lru_cache(maxsize=8)
def _list_web_static_images(subdir: str) -> tuple[str, ...]:
    """Paths relative to ``django_apps/web/static/`` for use with ``{% static %}``."""

    static_root = Path(settings.BASE_DIR) / "django_apps" / "web" / "static"
    folder = static_root / "web" / "img" / subdir
    if not folder.is_dir():
        return ()

    allowed = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    out: list[str] = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix.lower() in allowed:
            out.append(path.relative_to(static_root).as_posix())
    return tuple(out)


def _label_from_filename(rel_path: str) -> str:
    stem = Path(rel_path).stem.replace("-", " ")
    return stem.title()


def _build_gallery_assets(rel_paths: tuple[str, ...], section_label: str) -> list[dict[str, str]]:
    assets: list[dict[str, str]] = []
    for rel_path in rel_paths:
        filename = Path(rel_path).name
        title = _label_from_filename(rel_path)
        assets.append(
            {
                "path": rel_path,
                "title": title,
                "filename": filename,
                "section_label": section_label,
                "alt": f"{section_label}: {title}",
            }
        )
    return assets


def home(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "web/home.html",
        {
            "initial_code": HOME_INITIAL_SHAPE_CODE,
        },
    )


def gallery(request: HttpRequest) -> HttpResponse:
    screenshots = _list_web_static_images("screenshots")
    factory_templates = _list_web_static_images("factory-templates")
    screenshot_section_label = _("Screenshots")
    factory_section_label = _("Factory templates")
    screenshot_assets = _build_gallery_assets(screenshots, screenshot_section_label)
    factory_template_assets = _build_gallery_assets(factory_templates, factory_section_label)
    gallery_sections = [
        {
            "id": "screenshots",
            "index_label": "01",
            "title": screenshot_section_label,
            "description": _("Gameplay UI and factory moments from recent runs."),
            "group": "screenshots",
            "count": len(screenshot_assets),
            "featured": screenshot_assets[0] if screenshot_assets else None,
            "assets": screenshot_assets[1:] if len(screenshot_assets) > 1 else [],
        },
        {
            "id": "factory-templates",
            "index_label": "02",
            "title": factory_section_label,
            "description": _("Layout references captured from the in-game template browser."),
            "group": "factory-templates",
            "count": len(factory_template_assets),
            "featured": factory_template_assets[0] if factory_template_assets else None,
            "assets": factory_template_assets[1:] if len(factory_template_assets) > 1 else [],
        },
    ]
    return render(
        request,
        "web/gallery.html",
        {
            "screenshot_count": len(screenshots),
            "factory_template_count": len(factory_templates),
            "gallery_sections": gallery_sections,
        },
    )


def solver(request: HttpRequest) -> HttpResponse:
    shape_code = request.GET.get("code", "").strip()
    return render(
        request,
        "web/solver.html",
        {
            "shape_code": shape_code,
        },
    )


def pattern_lab(request: HttpRequest) -> HttpResponse:
    shape_code = request.GET.get("code", "").strip()
    analysis = analyze_pattern_lab_shape(shape_code) if shape_code else None
    return render(
        request,
        "web/pattern_lab.html",
        {
            "shape_code": shape_code,
            "analysis": analysis,
        },
    )


def _asteroid_miner_lab_page_context(
    blueprint_code: str, *, project: AsteroidProject | None = None
) -> dict[str, Any]:
    ctx = lab_page_context(project_id=int(project.pk) if project is not None else None)
    ctx["blueprint_code"] = blueprint_code
    ui_initial = dict(ctx.get("lab_ui_initial") or {})
    ui_initial["blueprintCode"] = blueprint_code
    ctx["lab_ui_initial"] = ui_initial
    ctx["lab_project_slug"] = str(project.slug) if project is not None else ""
    return ctx


def _lab_json_bundle_for_track_id(track_id: int | None, *, copy_code: str) -> dict[str, Any]:
    frames: list[dict[str, Any]] = []
    initial: dict[str, Any] = {}
    track: ReplayTrack | None = None
    if track_id is not None:
        track = (
            ReplayTrack.objects.filter(pk=int(track_id))
            .prefetch_related(
                Prefetch("frames", queryset=ReplayFrame.objects.order_by("frame_index", "id"))
            )
            .first()
        )
    if track is not None:
        frames, initial = build_lab_replay_payload(track)
    n = len(frames)
    fi = int(frames[0]["frame_index"]) if frames else 0
    ui = {
        "frame": fi,
        "totalFrames": n,
        "blueprintCode": copy_code,
        "hasReplayFrames": n > 0,
        "replayTrackId": int(track.pk) if track else None,
        "replayTrackKey": str(track.track_key) if track else None,
    }
    return {
        "lab_replay_frames_json": frames,
        "lab_initial_replay_frame_json": initial,
        "lab_ui_initial": ui,
    }


def _lab_optimization_append_debug(
    *,
    requested_map_input_id: int,
    client_replay_track_id: int,
    canonical_replay_track_id: int | None,
    append_track_id: int | None,
    response_track_id: int | None,
    corrected_stale_replay_track: bool,
    n0: int,
    appended: int,
    reason: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "requested_map_input_id": int(requested_map_input_id),
        "client_replay_track_id": int(client_replay_track_id),
        "canonical_replay_track_id": (
            int(canonical_replay_track_id) if canonical_replay_track_id is not None else None
        ),
        "append_track_id": int(append_track_id) if append_track_id is not None else None,
        "response_track_id": int(response_track_id) if response_track_id is not None else None,
        "corrected_stale_replay_track": bool(corrected_stale_replay_track),
        "n0": int(n0),
        "appended": int(appended),
        "reason": str(reason),
    }
    if extra:
        out.update(extra)
    return out


@require_POST
def asteroid_miner_layout_run_solver(request: HttpRequest) -> JsonResponse:
    """POST JSON: run bounded optimization and append Lab replay frames (single timeline)."""

    try:
        body = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "bad_json"}, status=400)

    slug = str(body.get("project_slug") or "").strip()
    tid_raw = body.get("replay_track_id")
    mid_raw = body.get("map_input_id")
    if not slug or tid_raw is None:
        return JsonResponse({"ok": False, "error": "missing_fields"}, status=400)

    try:
        replay_track_id = int(tid_raw)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "invalid_replay_track_id"}, status=400)

    proj = AsteroidProject.objects.filter(slug=slug).first()
    if proj is None:
        return JsonResponse({"ok": False, "error": "unknown_project"}, status=404)

    if mid_raw is not None:
        try:
            map_input_id = int(mid_raw)
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "error": "invalid_map_input_id"}, status=400)
        inp = AsteroidMapInput.objects.filter(pk=map_input_id, project_id=proj.pk).first()
    else:
        inp = AsteroidMapInput.objects.filter(project_id=proj.pk).order_by("-id").first()

    if inp is None:
        return JsonResponse({"ok": False, "error": "no_map_input"}, status=400)

    client_tid = int(replay_track_id)
    canonical = inspection_replay_track_for_map_input(inp)
    if canonical is None:
        return JsonResponse(
            {
                "ok": False,
                "error": "no_canonical_inspection_track",
                "lab_map_input_id": int(inp.pk),
                "optimization_append_debug": _lab_optimization_append_debug(
                    requested_map_input_id=int(inp.pk),
                    client_replay_track_id=client_tid,
                    canonical_replay_track_id=None,
                    append_track_id=None,
                    response_track_id=None,
                    corrected_stale_replay_track=False,
                    n0=0,
                    appended=0,
                    reason="no_canonical_inspection_track",
                ),
            },
            status=400,
        )

    effective_tid = int(canonical.pk)
    corrected_stale_replay_track = effective_tid != client_tid

    try:
        result = run_lab_solver_optimization_for_map_input(
            map_input_id=int(inp.pk),
            replay_track_id=effective_tid,
        )
    except ValueError as exc:
        return JsonResponse(
            {"ok": False, "error": "invalid_request", "message": str(exc)}, status=400
        )

    bundle = _lab_json_bundle_for_track_id(effective_tid, copy_code=inp.copy_code)
    response_tid = bundle.get("lab_ui_initial", {}).get("replayTrackId")
    if response_tid is not None:
        response_tid = int(response_tid)
    opt_extra = {k: v for k, v in result.debug.items() if k not in {"n0", "appended", "reason"}}
    opt_debug = _lab_optimization_append_debug(
        requested_map_input_id=int(inp.pk),
        client_replay_track_id=client_tid,
        canonical_replay_track_id=int(canonical.pk),
        append_track_id=effective_tid,
        response_track_id=response_tid,
        corrected_stale_replay_track=corrected_stale_replay_track,
        n0=result.inspection_frame_count_before,
        appended=result.appended,
        reason=str(result.debug.get("reason", "")),
        extra=opt_extra,
    )
    return JsonResponse(
        {
            "ok": True,
            "inspection_frame_count_before": result.inspection_frame_count_before,
            "appended_optimization_frames": result.appended,
            "lab_map_input_id": int(inp.pk),
            "optimization_append_debug": opt_debug,
            **bundle,
        }
    )


def asteroid_miner_layout_solver(request: HttpRequest) -> HttpResponse:
    """Asteroid mining lab shell (GET query ``code`` is ignored; use POST to persist)."""

    return render(
        request,
        "web/asteroid_miner_layout_solver.html",
        _asteroid_miner_lab_page_context("", project=None),
    )


def asteroid_miner_layout_project(request: HttpRequest, slug: str) -> HttpResponse:
    """Lab page for one persisted :class:`~django_apps.asteroid_lab.models.AsteroidProject`."""

    project = AsteroidProject.objects.filter(slug=slug).first()
    if project is None:
        raise Http404
    inp = AsteroidMapInput.objects.filter(project_id=project.pk).order_by("-created_at").first()
    blueprint_code = (inp.copy_code if inp else "") or ""
    return render(
        request,
        "web/asteroid_miner_layout_solver.html",
        _asteroid_miner_lab_page_context(blueprint_code, project=project),
    )


@require_POST
def asteroid_miner_layout_replay_frame_cell(request: HttpRequest) -> JsonResponse:
    """POST JSON: resolve one cell at world (x, y) for a persisted :class:`ReplayFrame`."""

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    def _bad(msg: str, status: int = 400) -> JsonResponse:
        return JsonResponse({"ok": False, "error": msg, "cell": None, "sources": {}}, status=status)

    try:
        replay_frame_id = int(body["replay_frame_id"])
        replay_track_id = int(body["replay_track_id"])
        x = int(body["x"])
        y = int(body["y"])
    except (KeyError, TypeError, ValueError):
        return _bad("missing_or_invalid_fields")

    if x == 0:
        return _bad("invalid_x_zero")

    project_slug = str(body.get("project_slug") or "").strip()

    frame = (
        ReplayFrame.objects.select_related("replay_track__project")
        .filter(pk=replay_frame_id)
        .first()
    )
    if frame is None:
        return _bad("replay_frame_not_found", 404)

    if int(frame.replay_track_id) != replay_track_id:
        return _bad("replay_track_mismatch", 403)

    if project_slug and frame.replay_track.project.slug != project_slug:
        return _bad("project_slug_mismatch", 403)

    ser = serialize_replay_frame(frame)
    cell, sources = lookup_cell_in_serialized_frame(ser, x, y)
    message = "" if cell is not None else "no_cell_at_xy"
    return JsonResponse(
        {
            "ok": True,
            "cell": cell,
            "sources": sources,
            "message": message,
            "frame_index": ser.get("frame_index"),
            "frame_key": ser.get("frame_key"),
        }
    )


@require_POST
def asteroid_miner_layout_create_project(request: HttpRequest) -> HttpResponse:
    """POST copy text, dedupe by digest, build inspection replay, redirect to slug URL (PRG)."""

    copy_code = (request.POST.get("copy_code") or "").strip()
    wants_json = "application/json" in (request.headers.get("Accept") or "").lower()
    stay_slug = (request.POST.get("project_slug") or "").strip()

    def _json_response(
        *,
        ok: bool,
        redirect_url: str,
        in_place: bool,
        copy_for_blueprint: str,
        replay_bundle: dict[str, Any],
        replay_ok: bool,
        error_message: str,
        status: int = 200,
    ) -> JsonResponse:
        body: dict[str, Any] = {
            "ok": ok,
            "redirect": redirect_url,
            "in_place": in_place,
            "blueprint_code": copy_for_blueprint,
            "replay_ok": replay_ok,
            "error_message": error_message,
        }
        body.update(replay_bundle)
        return JsonResponse(body, status=status)

    if stay_slug:
        stay_project = AsteroidProject.objects.filter(slug=stay_slug).first()
        if stay_project is None:
            messages.error(request, _("Unknown project."))
            if wants_json:
                return _json_response(
                    ok=False,
                    redirect_url=reverse("web:asteroid-miner-layout"),
                    in_place=False,
                    copy_for_blueprint=copy_code,
                    replay_bundle=_lab_json_bundle_for_track_id(None, copy_code=copy_code),
                    replay_ok=False,
                    error_message="unknown_project",
                    status=404,
                )
            return redirect(reverse("web:asteroid-miner-layout"))
        if not copy_code:
            redirect_url = reverse("web:asteroid-miner-layout-project", kwargs={"slug": stay_slug})
            if wants_json:
                return _json_response(
                    ok=False,
                    redirect_url=redirect_url,
                    in_place=False,
                    copy_for_blueprint="",
                    replay_bundle=_lab_json_bundle_for_track_id(None, copy_code=""),
                    replay_ok=False,
                    error_message="empty_copy",
                    status=400,
                )
            return redirect(redirect_url)
        inp = create_copy_code_map_input(stay_project, copy_code, source_label="")
        result = build_initial_replay_for_map_input(int(inp.pk), force=True)
        if result.status != "ok" and result.error_message:
            messages.error(request, result.error_message)
        redirect_url = reverse("web:asteroid-miner-layout-project", kwargs={"slug": stay_slug})
        bundle = _lab_json_bundle_for_track_id(result.replay_track_id, copy_code=copy_code)
        if wants_json:
            return _json_response(
                ok=True,
                redirect_url=redirect_url,
                in_place=True,
                copy_for_blueprint=copy_code,
                replay_bundle=bundle,
                replay_ok=result.status == "ok",
                error_message=result.error_message or "",
            )
        return redirect(redirect_url)

    if not copy_code:
        if wants_json:
            return _json_response(
                ok=False,
                redirect_url=reverse("web:asteroid-miner-layout"),
                in_place=False,
                copy_for_blueprint="",
                replay_bundle=_lab_json_bundle_for_track_id(None, copy_code=""),
                replay_ok=False,
                error_message="empty_copy",
                status=400,
            )
        return redirect(reverse("web:asteroid-miner-layout"))

    slug = resolve_or_create_project_slug_for_copy_code(copy_code, source_label="")
    project = AsteroidProject.objects.filter(slug=slug).first()
    result = None
    if project is not None:
        digest = content_sha256_for_copy_code(copy_code)
        inp = (
            AsteroidMapInput.objects.filter(project_id=project.pk, content_sha256=digest)
            .order_by("-created_at")
            .first()
        )
        if inp is None:
            inp = (
                AsteroidMapInput.objects.filter(project_id=project.pk)
                .order_by("-created_at")
                .first()
            )
        if inp is not None:
            result = build_initial_replay_for_map_input(int(inp.pk))
            if (
                result.status != "ok"
                and result.error_message
                and "force=True" in result.error_message
            ):
                result = build_initial_replay_for_map_input(int(inp.pk), force=True)
            if result.status != "ok" and result.error_message:
                messages.error(request, result.error_message)
    redirect_url = reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug})
    if wants_json:
        tid = getattr(result, "replay_track_id", None) if result is not None else None
        bundle = _lab_json_bundle_for_track_id(tid, copy_code=copy_code)
        err = (getattr(result, "error_message", "") or "") if result is not None else ""
        return _json_response(
            ok=True,
            redirect_url=redirect_url,
            in_place=False,
            copy_for_blueprint=copy_code,
            replay_bundle=bundle,
            replay_ok=getattr(result, "status", None) == "ok" if result is not None else False,
            error_message=err,
        )
    return redirect(redirect_url)


_KOFI_HOSTS = frozenset({"ko-fi.com", "www.ko-fi.com"})
_KOFI_SLUG = re.compile(r"^[A-Za-z0-9_-]+$")


def _support_tab_id(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    return slug[:48] if slug else "link"


def _kofi_widget_embed_src(profile_url: str) -> str | None:
    """Return Ko-fi HTML5 widget src for a profile URL, or None if not a Ko-fi profile."""
    if not profile_url:
        return None
    try:
        parsed = urlparse(profile_url)
    except ValueError:
        return None
    if (parsed.hostname or "").lower() not in _KOFI_HOSTS:
        return None
    segment = (parsed.path.strip("/").split("/") or [""])[0]
    if not segment or not _KOFI_SLUG.fullmatch(segment):
        return None
    return f"https://ko-fi.com/{segment}/?hidefeed=true&widget=true&embed=true"


def support(request: HttpRequest) -> HttpResponse:
    support_links: list[dict[str, str]] = []
    kofi_widget_embed_src = _kofi_widget_embed_src(settings.SUPPORT_KOFI_URL)
    if settings.SUPPORT_KOFI_URL and not kofi_widget_embed_src:
        support_links.append({"label": "Ko-fi", "url": settings.SUPPORT_KOFI_URL})
    if settings.SUPPORT_GITHUB_SPONSORS_URL:
        support_links.append(
            {"label": "GitHub Sponsors", "url": settings.SUPPORT_GITHUB_SPONSORS_URL}
        )
    if settings.SUPPORT_PATREON_URL:
        support_links.append({"label": "Patreon", "url": settings.SUPPORT_PATREON_URL})

    support_tabs: list[dict[str, Any]] = []
    if settings.SUPPORT_BCH_ADDRESS:
        support_tabs.append(
            {
                "id": "bch",
                "label": _("Bitcoin Cash (BCH)"),
                "kind": "bch",
                "address": settings.SUPPORT_BCH_ADDRESS,
                "qr_static": "web/images/support/bch_qr.png",
                "logo_static": "web/images/support/bch_logo.png",
                "badge_short": "BCH",
            }
        )
    if settings.SUPPORT_ETH_ADDRESS:
        support_tabs.append(
            {
                "id": "ethereum",
                "label": _("Ethereum (ETH)"),
                "kind": "eth",
                "address": settings.SUPPORT_ETH_ADDRESS,
                "qr_static": "web/images/support/eth_qr.png",
                "logo_static": "web/images/support/eth_logo.png",
                "badge_short": "ETH",
            }
        )
    if kofi_widget_embed_src:
        support_tabs.append(
            {
                "id": "kofi",
                "label": _("Ko-fi"),
                "kind": "kofi_embed",
                "embed_src": kofi_widget_embed_src,
            }
        )
    elif settings.SUPPORT_KOFI_URL:
        support_tabs.append(
            {
                "id": "kofi",
                "label": _("Ko-fi"),
                "kind": "kofi_link",
                "url": settings.SUPPORT_KOFI_URL,
            }
        )
    for link in support_links:
        if link["label"] == "Ko-fi":
            continue
        support_tabs.append(
            {
                "id": _support_tab_id(link["label"]),
                "label": link["label"],
                "kind": "external",
                "url": link["url"],
            }
        )

    return render(
        request,
        "web/support.html",
        {
            "support_links": support_links,
            "kofi_widget_embed_src": kofi_widget_embed_src,
            "support_tabs": support_tabs,
        },
    )


def graph_preview_cache(request: HttpRequest, filename: str) -> FileResponse | HttpResponse:
    del request
    if filename != Path(filename).name or not filename.endswith(".png"):
        raise Http404("Unknown graph preview.")

    cache_key = filename.removesuffix(".png")
    row = GraphPreviewImage.objects.filter(pk=cache_key).first()
    if row is not None and row.png:
        data = bytes(row.png)
        if png_bytes_are_valid(
            data,
            broken_sha256_hex=PlaywrightPngGraphPreviewRenderer.BROKEN_PNG_SHA256,
        ):
            return HttpResponse(data, content_type="image/png")

    cache_root = Path(settings.SOLVER_GRAPH_PREVIEW_CACHE_DIR)
    target = cache_root / filename
    if not target.is_file():
        raise Http404("Unknown graph preview.")

    return FileResponse(target.open("rb"), content_type="image/png")


def demo(request: HttpRequest) -> HttpResponse:
    try_code = request.GET.get("code", "").strip()

    return render(
        request,
        "web/demo.html",
        {
            "try_code": try_code,
            "parse_rows": build_demo_parse_rows(
                try_code=try_code, fixed_samples=DEMO_FIXED_SAMPLE_CODES
            ),
            "shape_catalog_rows": get_shape_catalog_rows(),
            "color_catalog_rows": get_color_catalog_rows(),
        },
    )
