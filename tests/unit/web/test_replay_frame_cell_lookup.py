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


def test_lookup_overlay_merged_on_top_of_full_map() -> None:
    """Optimization-style frame: HUD (x,y) must reflect cell_overlay on top of full_map."""
    ser = {
        "full_map": [
            {
                "x": 3,
                "y": -2,
                "cell_kind": "asteroid_fluid_field",
                "transport_kind": "none",
                "server_x": 2,
                "server_y": 8,
            },
        ],
        "diff": {},
        "cell_overlay_json": {
            "cells": [
                {
                    "x": 3,
                    "y": -2,
                    "layer": 0,
                    "cell_kind": "optimization_overlay",
                    "overlay_role": "route_path",
                    "severity": "info",
                },
            ],
        },
    }
    cell, sources = lookup_cell_in_serialized_frame(ser, 3, -2)
    assert cell is not None
    assert cell.get("cell_kind") == "optimization_overlay"
    assert cell.get("overlay_role") == "route_path"
    assert sources.get("full_map") is not None
    assert sources.get("overlay_cells_matched") == 1


def test_lookup_full_map_nonempty_but_xy_only_in_overlay() -> None:
    ser = {
        "full_map": [{"x": 0, "y": 0, "cell_kind": "field"}],
        "diff": {},
        "cell_overlay_json": {
            "cells": [
                {
                    "x": 5,
                    "y": 5,
                    "cell_kind": "optimization_overlay",
                    "overlay_role": "candidate_occupied",
                },
            ],
        },
    }
    cell, sources = lookup_cell_in_serialized_frame(ser, 5, 5)
    assert cell is not None
    assert cell.get("cell_kind") == "optimization_overlay"
    assert sources.get("overlay_cells_matched") == 1
    assert "full_map" not in sources
