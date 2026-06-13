"""Canvas paint plan respects Height layer (L) filter."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.replay_cell_index import cell_key
from tests.support.lab_replay_paint_plan import (
    CELL_KIND_STATIC_RELPATH,
    build_effective_cell_view_index,
    sprite_entries_from_paint_plan_frame,
)


def _frame_with_floor_shape_and_floor_belt() -> dict[str, object]:
    return {
        "frame_index": 1,
        "map_view": {
            "full_cells": [
                {
                    "x": 0,
                    "y": 0,
                    "kind": "asteroid_shape_field",
                    "transport": "none",
                },
                {
                    "x": 1,
                    "y": 0,
                    "kind": "space_belt",
                    "transport": "space_belt",
                    "tile_type": "SpaceBelt_Forward",
                },
            ],
        },
    }


def _frame_with_floor_shape_and_lift2_belt() -> dict[str, object]:
    return {
        "frame_index": 1,
        "map_view": {
            "full_cells": [
                {
                    "x": 0,
                    "y": 0,
                    "kind": "asteroid_shape_field",
                    "transport": "none",
                },
                {
                    "x": 1,
                    "y": 0,
                    "kind": "space_belt",
                    "transport": "space_belt",
                    "tile_type": "SpaceBelt_Lift2UpForward",
                },
            ],
        },
    }


def _frame_with_floor_shape_and_explicit_l2_belt() -> dict[str, object]:
    return {
        "frame_index": 1,
        "map_view": {
            "full_cells": [
                {
                    "x": 0,
                    "y": 0,
                    "kind": "asteroid_shape_field",
                    "transport": "none",
                },
                {
                    "x": 1,
                    "y": 0,
                    "kind": "space_belt",
                    "transport": "space_belt",
                    "tile_type": "SpaceBelt_Forward",
                    "layer": 2,
                },
            ],
        },
    }


def test_sprite_entries_include_all_layers_by_default() -> None:
    frame = _frame_with_floor_shape_and_floor_belt()
    index = build_effective_cell_view_index(frame)
    assert cell_key(0, 0, 0) in index
    assert cell_key(1, 0, 0) in index

    rels = {entry["rel"] for entry in sprite_entries_from_paint_plan_frame(frame)}
    assert CELL_KIND_STATIC_RELPATH["asteroid_shape_field"] in rels
    assert any("SpaceBelt" in rel for rel in rels)


def test_sprite_entries_hide_floor_when_layer_2_selected() -> None:
    frame = _frame_with_floor_shape_and_explicit_l2_belt()
    rels = {
        entry["rel"]
        for entry in sprite_entries_from_paint_plan_frame(frame, selected_map_z_layer=2)
    }
    assert CELL_KIND_STATIC_RELPATH["asteroid_shape_field"] not in rels
    assert any("SpaceBelt" in rel for rel in rels)


def test_sprite_entries_show_floor_belt_on_layer_0() -> None:
    frame = _frame_with_floor_shape_and_floor_belt()
    rels = {
        entry["rel"]
        for entry in sprite_entries_from_paint_plan_frame(frame, selected_map_z_layer=0)
    }
    assert CELL_KIND_STATIC_RELPATH["asteroid_shape_field"] in rels
    assert any("SpaceBelt" in rel for rel in rels)


def test_sprite_entries_show_lift2_belt_on_layer_1() -> None:
    frame = _frame_with_floor_shape_and_lift2_belt()
    index = build_effective_cell_view_index(frame)
    assert cell_key(1, 0, 1) in index
    rels = {
        entry["rel"]
        for entry in sprite_entries_from_paint_plan_frame(frame, selected_map_z_layer=1)
    }
    assert CELL_KIND_STATIC_RELPATH["asteroid_shape_field"] not in rels
    assert any("SpaceBelt" in rel for rel in rels)


def test_sprite_entries_hide_lift2_belt_when_layer_0_selected() -> None:
    frame = _frame_with_floor_shape_and_lift2_belt()
    rels = {
        entry["rel"]
        for entry in sprite_entries_from_paint_plan_frame(frame, selected_map_z_layer=0)
    }
    assert CELL_KIND_STATIC_RELPATH["asteroid_shape_field"] in rels
    assert not any("SpaceBelt" in rel for rel in rels)
