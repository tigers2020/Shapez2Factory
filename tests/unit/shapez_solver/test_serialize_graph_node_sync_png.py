"""serialize_graph_node(sync_png=False) contract + enrich overlay fields."""

from __future__ import annotations

from pathlib import Path

import pytest
from django.test import override_settings

from django_apps.shapez_solver.dto.solver_graph import SolverShapeNode
from django_apps.shapez_solver.services.macro_recipe_graph_visual import (
    _merge_preview_into_react_node,
    _shape_visual_overlay_by_node_id,
)
from django_apps.shapez_solver.view_graph_serialization import (
    build_preview_scene,
    serialize_graph_node,
)
from django_apps.web.models import GraphPreviewImage
from django_apps.web.services.graph_preview import (
    NoopGraphPreviewRenderer,
    PlaywrightPngGraphPreviewRenderer,
)


def test_sync_png_false_adds_warm_when_cache_miss() -> None:
    cache_dir = Path("F:/Python_Projects/shapez2Solver/.graph_preview_cache_sync_test")
    cache_dir.mkdir(parents=True, exist_ok=True)
    with override_settings(SOLVER_GRAPH_PREVIEW_CACHE_DIR=cache_dir):
        renderer = PlaywrightPngGraphPreviewRenderer()
        node = SolverShapeNode(
            id="n1",
            role="source",
            shape_code="CuCuCuCu",
            label="n1",
            quantity=1,
        )
        out = serialize_graph_node(node, renderer, sync_png=False)

    assert out["needs_warm"] is True
    assert isinstance(out["preview_cache_key"], str)
    assert len(out["preview_cache_key"]) == 24
    assert "preview_scene" in out
    assert out.get("preview_image_url") is None


@pytest.mark.django_db
def test_sync_png_false_hit_cached_png_db() -> None:
    cache_dir = Path("F:/Python_Projects/shapez2Solver/.graph_preview_cache_sync_hit_test")
    cache_dir.mkdir(parents=True, exist_ok=True)
    with override_settings(
        SOLVER_GRAPH_PREVIEW_CACHE_DIR=cache_dir,
        SOLVER_GRAPH_PREVIEW_STORAGE="database",
    ):
        renderer = PlaywrightPngGraphPreviewRenderer()
        scene = build_preview_scene("CuCuCuCu")
        ck = renderer.cache_key(scene)
        GraphPreviewImage.objects.create(cache_key=ck, png=b"png-bytes")

        node = SolverShapeNode(
            id="n1",
            role="source",
            shape_code="CuCuCuCu",
            label="n1",
            quantity=1,
        )
        out = serialize_graph_node(node, renderer, sync_png=False)

    assert isinstance(out.get("preview_image_url"), str)
    assert out["preview_image_url"].endswith(".png")
    assert out.get("needs_warm") is not True


def test_shape_visual_overlay_carries_warm_flags() -> None:
    visual = {
        "nodes": [
            {
                "id": "a",
                "kind": "shape",
                "preview_scene": {"normalized_code": "X", "cells": []},
                "preview_cache_key": "abc123",
                "needs_warm": True,
            }
        ]
    }
    m = _shape_visual_overlay_by_node_id(visual)
    assert m["a"]["needs_warm"] is True
    assert m["a"]["preview_cache_key"] == "abc123"


def test_merge_preview_into_react_preserves_warm() -> None:
    overlay = _shape_visual_overlay_by_node_id(
        {
            "nodes": [
                {
                    "id": "x",
                    "kind": "shape",
                    "preview_scene": {"normalized_code": "Y", "cells": []},
                    "needs_warm": True,
                    "preview_cache_key": "k",
                }
            ]
        }
    )
    react_node = {
        "id": "x",
        "type": "shape",
        "data": {"shape_code": "Y"},
    }
    merged = _merge_preview_into_react_node(react_node, overlay)
    data = merged["data"]
    assert isinstance(data, dict)
    assert data.get("needs_warm") is True
    assert data.get("preview_cache_key") == "k"


def test_noop_sync_png_false_always_warm() -> None:
    r = NoopGraphPreviewRenderer()
    node = SolverShapeNode(
        id="n1",
        role="source",
        shape_code="CuCuCuCu",
        label="n1",
        quantity=1,
    )
    out = serialize_graph_node(node, r, sync_png=False)
    assert out["needs_warm"] is True
