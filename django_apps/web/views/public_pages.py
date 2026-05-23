import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from django_apps.asteroid_lab.adapters.decode_adapter import AsteroidLabCopyDecodeError
from django_apps.asteroid_lab.models import (
    AsteroidMapInput,
    AsteroidProject,
    ReplayFrame,
    ReplayTrack,
)
from django_apps.asteroid_lab.services.input_service import (
    content_sha256_for_copy_code,
    upsert_map_input_for_project,
)
from django_apps.asteroid_lab.services.lab_map_reset_service import (
    LabMapResetErrorCode,
    reset_project_map_to_inspection_clean,
)
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    build_lab_optimization_milestone_frames_for_project,
)
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.project_service import (
    resolve_or_create_project_slug_for_copy_code,
)
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SolverRuntimeEntryErrorCode,
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)
from django_apps.game_data.snapshots.errors import SnapshotBuildError
from django_apps.shapez_core.services.lab_sprite_identifier_service import (
    build_lab_identifier_sprite_relpath_map,
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
from django_apps.web.services.asteroid_game_data_snapshot import build_asteroid_game_data_snapshot
from django_apps.web.services.asteroid_lab_page_context import (
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
    ctx["lab_identifier_sprite_paths"] = build_lab_identifier_sprite_relpath_map()
    return ctx


def _lab_json_bundle_for_track_id(track_id: int | None, *, copy_code: str) -> dict[str, Any]:
    frames: list[dict[str, Any]] = []
    track_metrics: dict[str, Any] = {
        "frame_count": 0,
        "replay_truncated": False,
        "truncation_reason": None,
        "dropped_frame_count": None,
        "diagnostic_reason": None,
    }
    initial: dict[str, Any] = {}
    track: ReplayTrack | None = None
    if track_id is not None:
        track = ReplayTrack.objects.filter(pk=int(track_id)).first()
    milestone_frames: list[dict[str, Any]] = []
    milestone_metrics: dict[str, Any] = {
        "track_key": None,
        "frame_count": 0,
        "event_types": [],
        "replay_truncated": False,
        "truncation_reason": None,
        "dropped_frame_count": None,
        "diagnostic_reason": None,
        "source_solver_run_id": None,
    }
    if track is not None and track.project_id is not None:
        project_id = int(track.project_id)
        frames, track_metrics = build_lab_replay_frames_for_project(project_id)
        # 3B v0: Section B binds to latest SolverRun on project (not inspection track_id).
        milestone_frames, milestone_metrics = build_lab_optimization_milestone_frames_for_project(
            project_id,
            run_key=None,
        )
        initial = dict(frames[0]) if frames else {}
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
        "replay_track_metrics": track_metrics,
        "lab_optimization_milestone_frames_json": milestone_frames,
        "lab_optimization_milestone_frame_count": len(milestone_frames),
        "lab_optimization_milestone_track_metrics": milestone_metrics,
    }


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


def _run_solver_request_config(request: HttpRequest) -> tuple[dict[str, Any], JsonResponse | None]:
    """Parse optional JSON POST body into runtime ``config`` (PR-K)."""

    if not request.body:
        return {}, None
    content_type = (request.content_type or "").lower()
    if "application/json" not in content_type:
        return {}, None
    try:
        parsed = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        err = JsonResponse({"ok": False, "error": "invalid_json"}, status=400)
        return {}, err
    if not isinstance(parsed, dict):
        err = JsonResponse({"ok": False, "error": "invalid_json"}, status=400)
        return {}, err
    return dict(parsed), None


@require_POST
def asteroid_miner_layout_project_run_solver(request: HttpRequest, slug: str) -> JsonResponse:
    """POST: run solver runtime pipeline for one project; JSON response (PR8 entry)."""

    run_config, config_err = _run_solver_request_config(request)
    if config_err is not None:
        return config_err

    project = AsteroidProject.objects.filter(slug=slug).first()
    if project is None:
        return JsonResponse(
            {
                "ok": False,
                "error_code": SolverRuntimeEntryErrorCode.PROJECT_NOT_FOUND.value,
                "solver_run_id": None,
                "lab_replay_frames_json": [],
                "replay_track_metrics": {
                    "frame_count": 0,
                    "replay_truncated": False,
                    "truncation_reason": None,
                    "dropped_frame_count": None,
                    "diagnostic_reason": None,
                },
                "solver_summary": {},
                "validation_passed": False,
            },
            status=404,
        )

    try:
        game_data_snapshot = build_asteroid_game_data_snapshot()
    except SnapshotBuildError as exc:
        return JsonResponse(
            {
                "ok": False,
                "error_code": exc.code.value,
                "solver_run_id": None,
                "lab_replay_frames_json": [],
                "replay_track_metrics": {
                    "frame_count": 0,
                    "replay_truncated": False,
                    "truncation_reason": None,
                    "dropped_frame_count": None,
                    "diagnostic_reason": None,
                },
                "solver_summary": {},
                "validation_passed": False,
            },
            status=400,
        )

    result = run_solver_runtime_for_project(
        int(project.pk),
        config=run_config,
        game_data_snapshot=game_data_snapshot,
    )
    body = entry_result_to_json_dict(result)
    if result.error_code in (
        SolverRuntimeEntryErrorCode.NO_MAP_INPUT,
        SolverRuntimeEntryErrorCode.PROJECT_NOT_FOUND,
    ):
        status = 404 if result.error_code == SolverRuntimeEntryErrorCode.PROJECT_NOT_FOUND else 400
        return JsonResponse(body, status=status)
    if result.error_code == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE:
        return JsonResponse(body, status=200)
    # RTTP may finish with validation failure but still persist a SolverRun (never 500).
    if result.solver_run_id is not None:
        return JsonResponse(body, status=200)
    if not result.ok:
        return JsonResponse(body, status=400)
    return JsonResponse(body, status=200)


@require_POST
def asteroid_miner_layout_project_reset_map(request: HttpRequest, slug: str) -> JsonResponse:
    """POST: purge runtime solver DB artifacts and rebuild inspection replay (map clean)."""

    project = AsteroidProject.objects.filter(slug=slug).first()
    if project is None:
        return JsonResponse(
            {
                "ok": False,
                "replay_ok": False,
                "error_code": LabMapResetErrorCode.PROJECT_NOT_FOUND.value,
                "error_message": LabMapResetErrorCode.PROJECT_NOT_FOUND.value,
                "lab_replay_frames_json": [],
                "replay_track_metrics": {
                    "frame_count": 0,
                    "replay_truncated": False,
                    "truncation_reason": None,
                    "dropped_frame_count": None,
                    "diagnostic_reason": None,
                },
            },
            status=404,
        )

    inp = (
        AsteroidMapInput.objects.filter(project_id=int(project.pk))
        .order_by("-created_at", "-id")
        .first()
    )
    copy_code = (inp.copy_code if inp else "") or ""

    result = reset_project_map_to_inspection_clean(int(project.pk))
    bundle = _lab_json_bundle_for_track_id(result.replay_track_id, copy_code=copy_code)
    body: dict[str, Any] = {
        "ok": result.status == "ok",
        "replay_ok": result.status == "ok",
        "error_message": result.error_message or "",
        "project_slug": slug,
        "run_solver_url": reverse(
            "web:asteroid-miner-layout-project-run-solver",
            kwargs={"slug": slug},
        ),
        "reset_map_url": reverse(
            "web:asteroid-miner-layout-project-reset-map",
            kwargs={"slug": slug},
        ),
        **bundle,
    }
    if result.status != "ok":
        body["error_code"] = (
            result.error_message
            if result.error_message in {e.value for e in LabMapResetErrorCode}
            else LabMapResetErrorCode.RESET_FAILED.value
        )
        return JsonResponse(body, status=400)
    return JsonResponse(body, status=200)


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
        project_slug: str = "",
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
        slug = project_slug.strip()
        if slug:
            body["project_slug"] = slug
            body["run_solver_url"] = reverse(
                "web:asteroid-miner-layout-project-run-solver",
                kwargs={"slug": slug},
            )
            body["reset_map_url"] = reverse(
                "web:asteroid-miner-layout-project-reset-map",
                kwargs={"slug": slug},
            )
        body.update(replay_bundle)
        return JsonResponse(body, status=status)

    def _respond_invalid_copy(*, redirect_url: str, in_place: bool) -> HttpResponse:
        messages.error(request, _("Invalid blueprint copy code."))
        if wants_json:
            return _json_response(
                ok=False,
                redirect_url=redirect_url,
                in_place=in_place,
                copy_for_blueprint=copy_code,
                replay_bundle=_lab_json_bundle_for_track_id(None, copy_code=copy_code),
                replay_ok=False,
                error_message="invalid_copy",
                status=400,
            )
        return redirect(redirect_url)

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
        try:
            inp, _created = upsert_map_input_for_project(stay_project, copy_code, source_label="")
        except AsteroidLabCopyDecodeError:
            return _respond_invalid_copy(
                redirect_url=reverse(
                    "web:asteroid-miner-layout-project", kwargs={"slug": stay_slug}
                ),
                in_place=True,
            )
        result = build_initial_replay_for_map_input(int(inp.pk), overwrite=True)
        if result.status != "ok" and result.error_message:
            messages.error(request, result.error_message)
        redirect_url = reverse("web:asteroid-miner-layout-project", kwargs={"slug": stay_slug})
        bundle = _lab_json_bundle_for_track_id(result.replay_track_id, copy_code=copy_code)
        if wants_json:
            return _json_response(
                ok=result.status == "ok",
                redirect_url=redirect_url,
                in_place=True,
                copy_for_blueprint=copy_code,
                replay_bundle=bundle,
                replay_ok=result.status == "ok",
                error_message=result.error_message or "",
                project_slug=stay_slug,
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

    try:
        slug = resolve_or_create_project_slug_for_copy_code(copy_code, source_label="")
    except AsteroidLabCopyDecodeError:
        return _respond_invalid_copy(
            redirect_url=reverse("web:asteroid-miner-layout"),
            in_place=False,
        )
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
            result = build_initial_replay_for_map_input(int(inp.pk), overwrite=True)
            if (
                result.status != "ok"
                and result.error_message
                and "force=True" in result.error_message
            ):
                result = build_initial_replay_for_map_input(int(inp.pk), overwrite=True)
            if result.status != "ok" and result.error_message:
                messages.error(request, result.error_message)
    redirect_url = reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug})
    if wants_json:
        tid = getattr(result, "replay_track_id", None) if result is not None else None
        bundle = _lab_json_bundle_for_track_id(tid, copy_code=copy_code)
        err = (getattr(result, "error_message", "") or "") if result is not None else ""
        replay_ok = getattr(result, "status", None) == "ok" if result is not None else False
        return _json_response(
            ok=replay_ok,
            redirect_url=redirect_url,
            in_place=False,
            copy_for_blueprint=copy_code,
            replay_bundle=bundle,
            replay_ok=replay_ok,
            error_message=err,
            project_slug=slug,
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
