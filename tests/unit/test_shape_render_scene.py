from __future__ import annotations

import dataclasses

import pytest

from shapez2_solver.application.shape_code_parser import parse_shape_code_list
from shapez2_solver.application.shape_render_scene import (
    ShapeRenderCell,
    ShapeRenderScene,
    build_shape_render_scene,
)
from shapez2_solver.domain.shape_pattern import QuadrantPosition


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
        ("default_rect", "u", "NE:L0"),
        ("default_circle", "u", "SE:L0"),
        ("default_star", "u", "SW:L0"),
        ("default_diamond", "u", "NW:L0"),
    ]


def test_shape_render_scene_keeps_position_and_solver_kinds() -> None:
    scene = _scene("WrCrRgSy")

    assert scene.cells[0] == ShapeRenderCell(
        layer_index=0,
        quadrant_index=0,
        position=QuadrantPosition.NE,
        shape_code="W",
        color_code="r",
        shape_kind="diamond",
        color_kind="red",
        mesh_key="default_diamond",
        material_key="r",
        transform_key="NE:L0",
    )


def test_shape_render_scene_is_immutable() -> None:
    scene = _scene("RuRuRuRu")

    assert dataclasses.is_dataclass(scene)
    assert dataclasses.is_dataclass(scene.cells[0])
    with pytest.raises(dataclasses.FrozenInstanceError):
        scene.normalized_code = "CuCuCuCu"
    with pytest.raises(dataclasses.FrozenInstanceError):
        scene.cells[0].mesh_key = "changed"
