"""Unit tests for replay frame (x, y) cell lookup (lab POST detail)."""

from __future__ import annotations

from django_apps.web.services.replay_frame_cell_lookup import lookup_cell_in_serialized_frame


def test_lookup_full_map_then_issue_merges() -> None:
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
    assert "issue_cell" in sources


def test_lookup_full_map_empty_cell_returns_none() -> None:
    ser = {
        "full_map": [{"x": 2, "y": 0, "cell_kind": "space_belt"}],
        "diff": {},
        "cell_overlay_json": {},
    }
    cell, _sources = lookup_cell_in_serialized_frame(ser, 9, 9)
    assert cell is None


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
