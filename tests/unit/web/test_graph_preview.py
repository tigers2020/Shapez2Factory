from __future__ import annotations

from pathlib import Path

from django.test import override_settings

from django_apps.web.services.graph_preview import (
    LightweightGraphPreviewRenderer,
    PlaywrightPngGraphPreviewRenderer,
    get_graph_preview_renderer,
)

_PREVIEW_SCENE = {
    "normalized_code": "CuRuSuWu",
    "cells": [
        {
            "layer_index": 0,
            "quadrant_index": 0,
            "position": "SW",
            "mesh_key": "default_rect",
            "material_key": "u",
        },
        {
            "layer_index": 0,
            "quadrant_index": 1,
            "position": "NW",
            "mesh_key": "default_circle",
            "material_key": "u",
        },
        {
            "layer_index": 0,
            "quadrant_index": 2,
            "position": "NE",
            "mesh_key": "default_star",
            "material_key": "u",
        },
        {
            "layer_index": 0,
            "quadrant_index": 3,
            "position": "SE",
            "mesh_key": "default_diamond",
            "material_key": "u",
        },
    ],
}


def test_lightweight_renderer_emits_accessible_svg_markup() -> None:
    preview = LightweightGraphPreviewRenderer().render(_PREVIEW_SCENE)

    assert preview.kind == "markup"
    assert preview.image_url is None
    assert preview.markup is not None
    assert '<svg class="mx-auto h-full w-full"' in preview.markup
    assert 'aria-label="Graph preview for CuRuSuWu"' in preview.markup


def test_renderer_selection_can_choose_lightweight() -> None:
    with override_settings(SOLVER_GRAPH_PREVIEW_RENDERER="lightweight"):
        renderer = get_graph_preview_renderer()

        assert isinstance(renderer, LightweightGraphPreviewRenderer)


def test_renderer_selection_defaults_to_png_renderer() -> None:
    renderer = get_graph_preview_renderer()

    assert isinstance(renderer, PlaywrightPngGraphPreviewRenderer)


def test_renderer_selection_can_choose_png_renderer() -> None:
    with override_settings(
        SOLVER_GRAPH_PREVIEW_RENDERER="playwright_png",
        SOLVER_GRAPH_PREVIEW_CACHE_DIR=Path(
            "F:/Python_Projects/shapez2Solver/.graph_preview_cache_test"
        ),
    ):
        renderer = get_graph_preview_renderer()

        assert isinstance(renderer, PlaywrightPngGraphPreviewRenderer)


def test_png_renderer_cache_key_is_stable_and_versioned() -> None:
    with override_settings(
        SOLVER_GRAPH_PREVIEW_CACHE_DIR=Path(
            "F:/Python_Projects/shapez2Solver/.graph_preview_cache_test"
        )
    ):
        renderer = PlaywrightPngGraphPreviewRenderer()
        first = renderer.cache_key(_PREVIEW_SCENE)
        second = renderer.cache_key(_PREVIEW_SCENE)
        changed = renderer.cache_key({**_PREVIEW_SCENE, "normalized_code": "RuRuRuRu"})

    assert first == second
    assert first != changed


def test_png_renderer_falls_back_to_lightweight_markup() -> None:
    cache_dir = Path("F:/Python_Projects/shapez2Solver/.graph_preview_cache_fallback_test")
    cache_dir.mkdir(parents=True, exist_ok=True)

    class FailingRenderer(PlaywrightPngGraphPreviewRenderer):
        def _invoke_playwright_prerender(
            self, preview_scene: dict[str, object], cache_path: Path
        ) -> bool:
            del preview_scene
            del cache_path
            return False

    with override_settings(SOLVER_GRAPH_PREVIEW_CACHE_DIR=cache_dir):
        preview = FailingRenderer().render(_PREVIEW_SCENE)

    assert preview.kind == "markup"
    assert preview.image_url is None
    assert preview.markup is not None


def test_png_renderer_uses_cached_image_when_available() -> None:
    cache_dir = Path("F:/Python_Projects/shapez2Solver/.graph_preview_cache_test")
    cache_dir.mkdir(parents=True, exist_ok=True)
    with override_settings(SOLVER_GRAPH_PREVIEW_CACHE_DIR=cache_dir):
        renderer = PlaywrightPngGraphPreviewRenderer()
        cache_key = renderer.cache_key(_PREVIEW_SCENE)
        cache_path = cache_dir / f"{cache_key}.png"
        cache_path.write_bytes(b"png")
        image_url = renderer.render(_PREVIEW_SCENE).image_url

    assert image_url is not None
    assert image_url.endswith(".png")
