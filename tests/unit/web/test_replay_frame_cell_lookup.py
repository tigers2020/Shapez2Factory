"""Unit tests for replay frame (x, y) cell lookup (lab POST detail)."""

from __future__ import annotations

from django_apps.web.services.replay_frame_cell_lookup import lookup_cell_in_serialized_frame


def test_lookup_full_map_then_issue_same_cell_kind_merge_contract() -> None:
    ser = {
        "full_map": [
            {"x": 1, "y": 0, "cell_kind": "fluid_miner", "layer": None},
        ],
        "diff": {"removed": [], "added": [], "changed": []},
        "cell_overlay_json": {
            "issue_cells": [{"x": 1, "y": 0, "issue_code": "E_TEST", "cell_kind": "fluid_miner"}],
        },
    }
    cell, sources = lookup_cell_in_serialized_frame(ser, 1, 0)
    assert cell is not None
    assert cell.get("issue_code") == "E_TEST"
    assert cell.get("cell_kind") == "fluid_miner"
    assert cell.get("issue_original_cell_kind") == "fluid_miner"
    assert "issue_cell" in sources


def test_lookup_field_plus_issue_extension_merged_physical_from_full_map() -> None:
    ser = {
        "full_map": [
            {
                "x": 4,
                "y": -8,
                "layer": None,
                "cell_kind": "asteroid_fluid_field",
                "transport_kind": "none",
                "tile_type": "",
                "rotation": 0,
                "server_x": 2,
                "server_y": 8,
            },
        ],
        "diff": {"removed": [], "added": [], "changed": []},
        "cell_overlay_json": {
            "issue_cells": [
                {
                    "x": 4,
                    "y": -8,
                    "layer": None,
                    "cell_kind": "fluid_miner_extension",
                    "issue_code": "extension_no_adjacent_transport",
                    "severity": "error",
                    "overlay_role": "issue",
                    "equipment_id": "4,-8,null",
                },
            ],
        },
    }
    cell, _sources = lookup_cell_in_serialized_frame(ser, 4, -8)
    assert cell is not None
    assert cell.get("cell_kind") == "asteroid_fluid_field"
    assert cell.get("transport_kind") == "none"
    assert cell.get("server_x") == 2
    assert cell.get("server_y") == 8
    assert cell.get("issue_original_cell_kind") == "fluid_miner_extension"
    assert cell.get("issue_equipment_id") == "4,-8,null"
    assert cell.get("issue_code") == "extension_no_adjacent_transport"


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
