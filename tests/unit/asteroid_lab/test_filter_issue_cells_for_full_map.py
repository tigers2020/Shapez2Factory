"""filter_issue_cells_for_full_map: stale equipment issue rows vs reconstruction full_map."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.snapshot_map_replay import filter_issue_cells_for_full_map


def test_filter_removes_stale_equipment_extension_vs_field() -> None:
    full_map = [{"x": 1, "y": 0, "layer": None, "cell_kind": "asteroid_fluid_field"}]
    raw = [
        {
            "x": 1,
            "y": 0,
            "layer": None,
            "cell_kind": "fluid_miner_extension",
            "issue_code": "extension_no_adjacent_transport",
            "severity": "error",
            "overlay_role": "issue",
            "equipment_id": "1,0,null",
        },
    ]
    out = filter_issue_cells_for_full_map(raw, full_map)
    assert out == []


def test_filter_keeps_non_equipment_issue() -> None:
    full_map = [{"x": 2, "y": 0, "layer": None, "cell_kind": "space_belt"}]
    row = {
        "x": 2,
        "y": 0,
        "layer": None,
        "cell_kind": "space_belt",
        "issue_code": "mixed_transport_nearby",
        "severity": "warning",
        "overlay_role": "issue",
        "equipment_id": "",
    }
    out = filter_issue_cells_for_full_map([row], full_map)
    assert len(out) == 1
    assert out[0]["issue_code"] == "mixed_transport_nearby"


def test_filter_keeps_equipment_issue_when_cell_kind_matches() -> None:
    full_map = [{"x": 3, "y": 0, "layer": None, "cell_kind": "fluid_miner"}]
    row = {
        "x": 3,
        "y": 0,
        "layer": None,
        "cell_kind": "fluid_miner",
        "issue_code": "miner_no_adjacent_transport",
        "severity": "error",
        "overlay_role": "issue",
        "equipment_id": "3,0,null",
    }
    out = filter_issue_cells_for_full_map([row], full_map)
    assert len(out) == 1
