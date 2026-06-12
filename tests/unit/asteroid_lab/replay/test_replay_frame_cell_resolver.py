"""Unit tests for serialized replay frame (x, y) cell resolver."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.replay_frame_cell_resolver import (
    lookup_effective_cell_in_serialized_frame,
)


def test_lookup_full_map_empty_cell_returns_none() -> None:
    ser = {
        "full_map": [{"x": 2, "y": 0, "cell_kind": "space_belt"}],
        "diff": {},
        "cell_overlay_json": {},
    }
    effective, _sources = lookup_effective_cell_in_serialized_frame(ser, 9, 9)
    assert effective is None


def test_lookup_removed_transport_coord_has_no_full_map_source() -> None:
    """step0-style frame: pipe only in diff.removed, not in full_map — no sources['full_map']."""
    ser = {
        "full_map": [{"x": 1, "y": 0, "cell_kind": "fluid_miner", "layer": None}],
        "diff": {
            "removed": [
                {
                    "x": 2,
                    "y": 0,
                    "layer": None,
                    "cell_kind": "space_pipe",
                    "tile_type": "SpacePipe_Forward",
                    "transport_kind": "fluid_pipe",
                },
            ],
            "added": [],
            "changed": [],
        },
        "cell_overlay_json": {},
    }
    effective, sources = lookup_effective_cell_in_serialized_frame(ser, 2, 0)
    assert effective is not None
    assert "full_map" not in sources
    assert sources.get("diff_removed", {}).get("cell_kind") == "space_pipe"
    assert effective["transport"]["kind"] == "space_pipe"
    assert effective["transport"]["tile_id"] == "SpacePipe_Forward"


def test_lookup_overlay_only_matches_last() -> None:
    ser: dict = {"full_map": [], "cell_overlay_json": {}}
    ser["cell_overlay_json"] = {
        "cells": [
            {"x": -1, "y": 0, "cell_kind": "space_belt"},
            {"x": -1, "y": 0, "cell_kind": "space_pipe"},
        ],
    }
    effective, sources = lookup_effective_cell_in_serialized_frame(ser, -1, 0)
    assert effective is not None
    assert effective["transport"]["kind"] == "space_pipe"
    assert sources.get("overlay_cells_matched") == 2


def test_lookup_overlay_fallback_when_full_map_misses_xy() -> None:
    """Non-empty ``full_map`` but target only in ``cell_overlay_json.cells`` (Lab parity)."""

    ser = {
        "full_map": [{"x": 1, "y": 0, "cell_kind": "fluid_miner", "layer": None}],
        "diff": {},
        "cell_overlay_json": {
            "cells": [
                {
                    "x": 2,
                    "y": 0,
                    "cell_kind": "space_pipe",
                    "tile_type": "SpacePipe_Forward",
                    "layer": None,
                },
            ],
        },
    }
    effective, sources = lookup_effective_cell_in_serialized_frame(ser, 2, 0)
    assert effective is not None
    assert effective["transport"]["kind"] == "space_pipe"
    assert effective["transport"]["tile_id"] == "SpacePipe_Forward"
    assert sources.get("overlay_cells_matched") == 1


def test_lookup_full_map_two_rows_same_xy_last_row_wins_in_sources() -> None:
    """All ``full_map`` rows at (x,y) merge; resolver keeps last row in sources['full_map']."""

    ser = {
        "full_map": [
            {"x": 1, "y": 0, "cell_kind": "first", "layer": None, "rotation": 0},
            {"x": 1, "y": 0, "cell_kind": "second", "tile_type": "T9", "layer": 1},
        ],
        "diff": {},
        "cell_overlay_json": {},
    }
    effective, sources = lookup_effective_cell_in_serialized_frame(ser, 1, 0)
    assert effective is not None
    assert sources.get("full_map", {}).get("cell_kind") == "second"
    assert effective["coord"]["layer"] == 1


def test_lookup_synthetic_lab_empty_inside_raw_bbox() -> None:
    bbox = {
        "min_x": 0,
        "max_x": 5,
        "min_y": 0,
        "max_y": 3,
    }
    ser = {
        "full_map": [{"x": 99, "y": 99, "cell_kind": "fluid_miner", "layer": None}],
        "diff": {},
        "cell_overlay_json": {},
        "summary": {"bbox": bbox},
    }
    effective, sources = lookup_effective_cell_in_serialized_frame(ser, 1, 0)
    assert effective is not None
    assert effective["coord"]["x"] == 1
    assert effective["coord"]["y"] == 0
    assert sources.get("lab_synthetic") == "empty_island_cell"


def test_lookup_synthetic_lab_empty_inside_island_bbox_only() -> None:
    bbox = {"min_x": -2, "max_x": 2, "min_y": 0, "max_y": 1}
    ser = {
        "full_map": [],
        "diff": {},
        "cell_overlay_json": {},
        "summary": {"bbox": bbox},
    }
    effective, sources = lookup_effective_cell_in_serialized_frame(ser, 0, 0)
    assert effective is not None
    assert effective["coord"]["x"] == 0
    assert effective["coord"]["y"] == 0
    assert sources.get("lab_synthetic") == "empty_island_cell"


def test_lookup_does_not_infer_empty_from_all_full_map_xy() -> None:
    ser = {
        "full_map": [
            {"x": 0, "y": 0, "cell_kind": "space_belt"},
            {"x": 10, "y": 0, "cell_kind": "space_belt"},
        ],
        "diff": {},
        "cell_overlay_json": {},
    }
    effective, sources = lookup_effective_cell_in_serialized_frame(ser, 5, 0)
    assert effective is None
    assert "lab_synthetic" not in sources


def test_lookup_synthetic_none_outside_raw_bbox() -> None:
    bbox = {
        "min_x": 0,
        "max_x": 1,
        "min_y": 0,
        "max_y": 0,
    }
    ser = {
        "full_map": [],
        "diff": {},
        "cell_overlay_json": {},
        "metric_snapshot_json": {"bbox": bbox},
    }
    effective, _sources = lookup_effective_cell_in_serialized_frame(ser, 5, 0)
    assert effective is None
