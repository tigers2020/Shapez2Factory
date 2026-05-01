from functools import lru_cache
from pathlib import Path
from typing import Any

from django.conf import settings
from django.shortcuts import render

from django_apps.web.services.shape_svg_renderer import render_shape_pattern_svg
from shapez2_solver.application.shape_code_parser import ShapeCodeParseError, parse_shape_code_list
from shapez2_solver.domain.shape_catalog import COLOR_KINDS, SHAPE_KINDS
from shapez2_solver.domain.shape_pattern import NormalizedShapePattern


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


def home(request):
    return render(request, "web/home.html")


def gallery(request):
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


def _serialize_pattern(p: NormalizedShapePattern) -> dict[str, Any]:
    return {
        "raw_code": p.raw_code,
        "normalized_code": p.normalized_code,
        "layers": [
            {
                "layer_index": lyr.layer_index,
                "cells": [
                    {
                        "quadrant_index": c.quadrant_index,
                        "position": c.position.value,
                        "shape_code": c.shape_code,
                        "color_code": c.color_code,
                        "shape_kind": c.shape_kind,
                        "color_kind": c.color_kind,
                        "raw_token": c.raw_token,
                    }
                    for c in lyr.cells
                ],
            }
            for lyr in p.layers
        ],
    }


def _demo_parse_row(code: str) -> dict[str, Any]:
    try:
        patterns = parse_shape_code_list(code)
        return {
            "input": code,
            "ok": True,
            "error": None,
            "patterns": [
                {
                    **_serialize_pattern(p),
                    "preview_svg": render_shape_pattern_svg(p, size=192),
                }
                for p in patterns
            ],
        }
    except ShapeCodeParseError as exc:
        return {
            "input": code,
            "ok": False,
            "error": str(exc),
            "patterns": [],
        }


def demo(request):
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
    parse_rows: list[dict[str, Any]] = []
    if try_code:
        parse_rows.append(_demo_parse_row(try_code))
    for sample in fixed_samples:
        if try_code and sample == try_code:
            continue
        parse_rows.append(_demo_parse_row(sample))

    shape_catalog_rows = sorted(
        SHAPE_KINDS.values(),
        key=lambda sk: (sk.empty, sk.code.lower()),
    )
    color_catalog_rows = sorted(
        COLOR_KINDS.values(),
        key=lambda ck: (ck.empty, ck.code),
    )

    return render(
        request,
        "web/demo.html",
        {
            "try_code": try_code,
            "parse_rows": parse_rows,
            "shape_catalog_rows": shape_catalog_rows,
            "color_catalog_rows": color_catalog_rows,
        },
    )
