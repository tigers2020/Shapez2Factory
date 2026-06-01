"""Unit tests for replay frame (x, y) cell lookup (lab POST detail)."""

from __future__ import annotations

from django_apps.web.services.replay_frame_cell_lookup import lookup_cell_in_serialized_frame


def test_lookup_full_map_empty_cell_returns_none() -> None:
    ser = {
        "full_map": [{"x": 2, "y": 0, "cell_kind": "space_belt"}],
        "diff": {},
        "cell_overlay_json": {},
    }
    cell, _sources = lookup_cell_in_serialized_frame(ser, 9, 9)
    assert cell is None


def test_lookup_removed_transport_coord_has_no_full_map_source() -> None:
    """step0-style frame: pipe only in diff.removed, not in full_map ??no sources['full_map']."""
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
    cell, sources = lookup_cell_in_serialized_frame(ser, 2, 0)
    assert "full_map" not in sources
    assert sources.get("diff_removed", {}).get("cell_kind") == "space_pipe"
    assert cell is not None
    assert cell.get("cell_kind") == "space_pipe"


def test_lookup_overlay_only_matches_last() -> None:
    ser: dict = {"full_map": [], "cell_overlay_json": {}}
    ser["cell_overlay_json"] = {
        "cells": [
            {"x": -1, "y": 0, "cell_kind": "space_belt"},
            {"x": -1, "y": 0, "cell_kind": "space_pipe"},
        ],
    }
    cell, sources = lookup_cell_in_serialized_frame(ser, -1, 0)
    assert cell is not None
    assert cell.get("cell_kind") == "space_pipe"
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
    cell, sources = lookup_cell_in_serialized_frame(ser, 2, 0)
    assert cell is not None
    assert cell.get("cell_kind") == "space_pipe"
    assert sources.get("overlay_cells_matched") == 1


def test_lookup_full_map_two_rows_same_xy_merge_order() -> None:
    """All ``full_map`` rows at (x,y) merge; later dict keys overwrite earlier (``dict.update``)."""

    ser = {
        "full_map": [
            {"x": 1, "y": 0, "cell_kind": "first", "layer": None, "rotation": 0},
            {"x": 1, "y": 0, "cell_kind": "second", "tile_type": "T9", "layer": 1},
        ],
        "diff": {},
        "cell_overlay_json": {},
    }
    cell, _sources = lookup_cell_in_serialized_frame(ser, 1, 0)
    assert cell.get("cell_kind") == "second"
    assert cell.get("tile_type") == "T9"


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
    cell, sources = lookup_cell_in_serialized_frame(ser, 1, 0)
    assert cell is not None
    assert cell.get("_lab_synthetic") is True
    assert cell.get("cell_kind") == "lab_empty"
    assert sources.get("lab_synthetic") == "empty_island_cell"


def test_lookup_synthetic_lab_empty_inside_island_bbox_only() -> None:
    bbox = {"min_x": -2, "max_x": 2, "min_y": 0, "max_y": 1}
    ser = {
        "full_map": [],
        "diff": {},
        "cell_overlay_json": {},
        "summary": {"bbox": bbox},
    }
    cell, sources = lookup_cell_in_serialized_frame(ser, 0, 0)
    assert cell is not None
    assert cell.get("_lab_synthetic") is True
    assert cell.get("cell_kind") == "lab_empty"
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
    cell, sources = lookup_cell_in_serialized_frame(ser, 5, 0)
    assert cell is None
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
    cell, _sources = lookup_cell_in_serialized_frame(ser, 5, 0)
    assert cell is None
