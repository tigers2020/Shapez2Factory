import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from django_apps.asteroid_lab.models import AsteroidMapInput, AsteroidProject
from django_apps.asteroid_lab.services.input_service import content_sha256_for_copy_code
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
from django_apps.web.services.asteroid_lab_page_context import lab_page_context
from django_apps.web.services.graph_preview import (
    PlaywrightPngGraphPreviewRenderer,
    png_bytes_are_valid,
)


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


def _asteroid_miner_lab_page_context(blueprint_code: str) -> dict[str, Any]:
    ctx = lab_page_context()
    ctx["blueprint_code"] = blueprint_code
    ui_initial = dict(ctx.get("lab_ui_initial") or {})
    ui_initial["blueprintCode"] = blueprint_code
    ctx["lab_ui_initial"] = ui_initial
    return ctx


def asteroid_miner_layout_solver(request: HttpRequest) -> HttpResponse:
    """Asteroid mining lab shell (GET query ``code`` is ignored; use POST to persist)."""

    return render(
        request,
        "web/asteroid_miner_layout_solver.html",
        _asteroid_miner_lab_page_context(""),
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
        _asteroid_miner_lab_page_context(blueprint_code),
    )


@require_POST
def asteroid_miner_layout_create_project(request: HttpRequest) -> HttpResponse:
    """POST copy text, dedupe by digest, build inspection replay, redirect to slug URL (PRG)."""

    copy_code = (request.POST.get("copy_code") or "").strip()
    if not copy_code:
        return redirect(reverse("web:asteroid-miner-layout"))
    slug = resolve_or_create_project_slug_for_copy_code(copy_code, source_label="")
    project = AsteroidProject.objects.filter(slug=slug).first()
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
            if result.status != "ok" and result.error_message:
                messages.error(request, result.error_message)
    return redirect(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))


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
