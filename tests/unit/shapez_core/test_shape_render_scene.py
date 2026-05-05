from __future__ import annotations

import dataclasses
from typing import Any, cast

import pytest

from django_apps.shapez_core.domain.shape_pattern import QuadrantPosition
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_render_scene import (
    ShapeRenderCell,
    ShapeRenderScene,
    build_shape_render_scene,
)


def _scene(code: str) -> ShapeRenderScene:
    pattern = parse_shape_code_list(code)[0]
    return build_shape_render_scene(pattern)


def test_shape_render_scene_preserves_normalized_code() -> None:
    scene = _scene("RuRuRuRu:WrCrRgSy")

    assert scene.normalized_code == "RuRuRuRu:WrCrRgSy"


def test_shape_render_scene_omits_empty_cells() -> None:
    scene = _scene("Ru------")

    assert len(scene.cells) == 1
    assert scene.cells[0].shape_code == "R"
    assert all(cell.shape_code != "-" for cell in scene.cells)


def test_shape_render_scene_counts_multilayer_non_empty_cells() -> None:
    scene = _scene("RuRuRuRu:WrCrRgSy")

    assert len(scene.cells) == 8
    assert [cell.layer_index for cell in scene.cells] == [0, 0, 0, 0, 1, 1, 1, 1]


def test_shape_render_scene_keys_are_stable() -> None:
    scene = _scene("RuCuSuWu")

    assert [(cell.mesh_key, cell.material_key, cell.transform_key) for cell in scene.cells] == [
        ("default_rect", "u", "SW:L0"),
        ("default_circle", "u", "NW:L0"),
        ("default_star", "u", "NE:L0"),
        ("default_diamond", "u", "SE:L0"),
    ]


def test_shape_render_scene_crystal_layer_maps_to_default_crystal_mesh() -> None:
    scene = _scene("cccccccc")

    assert len(scene.cells) == 4
    assert all(c.mesh_key == "default_crystal" for c in scene.cells)
    assert all(c.material_key == "c" for c in scene.cells)
    assert all(c.shape_code == "c" for c in scene.cells)


def test_shape_render_scene_keeps_position_and_solver_kinds() -> None:
    scene = _scene("WrCrRgSy")

    assert scene.cells[0] == ShapeRenderCell(
        layer_index=0,
        quadrant_index=0,
        position=QuadrantPosition.SW,
        shape_code="W",
        color_code="r",
        shape_kind="diamond",
        color_kind="red",
        mesh_key="default_diamond",
        material_key="r",
        transform_key="SW:L0",
    )


def test_shape_render_scene_is_immutable() -> None:
    scene = _scene("RuRuRuRu")

    assert dataclasses.is_dataclass(scene)
    assert dataclasses.is_dataclass(scene.cells[0])
    mutable_scene = cast(Any, scene)
    mutable_cell = cast(Any, scene.cells[0])
    with pytest.raises(dataclasses.FrozenInstanceError):
        mutable_scene.normalized_code = "CuCuCuCu"
    with pytest.raises(dataclasses.FrozenInstanceError):
        mutable_cell.mesh_key = "changed"
