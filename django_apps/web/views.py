from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from django_apps.shapez_core.services.preview_service import (
    build_demo_parse_rows,
    get_color_catalog_rows,
    get_shape_catalog_rows,
)
from django_apps.shapez_solver.services.pattern_lab_service import analyze_pattern_lab_shape


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
            "initial_code": "CuRuSuWu",
        },
    )


def gallery(request: HttpRequest) -> HttpResponse:
    screenshots = _list_web_static_images("screenshots")
    factory_templates = _list_web_static_images("factory-templates")
    screenshot_assets = _build_gallery_assets(screenshots, "Screenshots")
    factory_template_assets = _build_gallery_assets(factory_templates, "Factory templates")
    gallery_sections = [
        {
            "id": "screenshots",
            "index_label": "01",
            "title": "Screenshots",
            "description": "Gameplay UI and factory moments from recent runs.",
            "group": "screenshots",
            "count": len(screenshot_assets),
            "featured": screenshot_assets[0] if screenshot_assets else None,
            "assets": screenshot_assets[1:] if len(screenshot_assets) > 1 else [],
        },
        {
            "id": "factory-templates",
            "index_label": "02",
            "title": "Factory templates",
            "description": "Layout references captured from the in-game template browser.",
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
            "nav_tone": "mono",
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


def support(request: HttpRequest) -> HttpResponse:
    support_links: list[dict[str, str]] = []
    if settings.SUPPORT_KOFI_URL:
        support_links.append({"label": "Ko-fi", "url": settings.SUPPORT_KOFI_URL})
    if settings.SUPPORT_GITHUB_SPONSORS_URL:
        support_links.append(
            {"label": "GitHub Sponsors", "url": settings.SUPPORT_GITHUB_SPONSORS_URL}
        )
    if settings.SUPPORT_PATREON_URL:
        support_links.append({"label": "Patreon", "url": settings.SUPPORT_PATREON_URL})
    return render(
        request,
        "web/support.html",
        {"support_links": support_links},
    )


def graph_preview_cache(request: HttpRequest, filename: str) -> FileResponse:
    del request
    if filename != Path(filename).name or not filename.endswith(".png"):
        raise Http404("Unknown graph preview.")

    cache_root = Path(settings.SOLVER_GRAPH_PREVIEW_CACHE_DIR)
    target = cache_root / filename
    if not target.is_file():
        raise Http404("Unknown graph preview.")

    return FileResponse(target.open("rb"), content_type="image/png")


def demo(request: HttpRequest) -> HttpResponse:
    try_code = request.GET.get("code", "").strip()
    fixed_samples = (
        "SuSuSuSu",
        "[RuRuRuRu, WrCrRgSy]",
        "RuRuRuRu:WrCrRgSy",
        "--RuRuRu",
        "CuCuCuCu",
        "PuPuPuPu",
        "XuXuXuXu",
        "PrPrPrPr",
    )

    return render(
        request,
        "web/demo.html",
        {
            "try_code": try_code,
            "parse_rows": build_demo_parse_rows(try_code=try_code, fixed_samples=fixed_samples),
            "shape_catalog_rows": get_shape_catalog_rows(),
            "color_catalog_rows": get_color_catalog_rows(),
        },
    )
