"""Dump-verified speed blob shapes (no DB)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from django_apps.game_data.services.simulation_speed_extract import (
    DUMP_TYPE_BUFFABLE,
    DUMP_TYPE_MULTIPLE,
    SPEED_PARAMETER_NAMES,
    SpeedRoute,
    classify_speed_entry,
    parameter_matches_route,
    parse_buffable_speed_blob,
    parse_multiple_speed_blob,
    validate_buffable_shape,
    validate_multiple_shape,
)

FIXTURE = (
    Path(__file__).resolve().parents[3] / "documents" / "game_data" / "simulation_systems.json"
)


def _load_rows() -> list[dict]:
    if not FIXTURE.is_file():
        pytest.skip("simulation_systems.json missing")
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_full_dump_speed_blob_inventory() -> None:
    rows = _load_rows()
    counts = {k: 0 for k in SPEED_PARAMETER_NAMES}
    mismatches: list[str] = []
    invalid: list[str] = []

    for i, row in enumerate(rows):
        params = row.get("simulation_parameters") or {}
        for pname in SPEED_PARAMETER_NAMES:
            if pname not in params:
                continue
            blob = params[pname]
            assert isinstance(blob, dict)
            counts[pname] += 1
            route, dtype = classify_speed_entry(pname, blob)
            assert route != SpeedRoute.SKIP
            assert parameter_matches_route(pname, route), (i, pname, dtype)
            if route == SpeedRoute.BUFFABLE:
                assert dtype == DUMP_TYPE_BUFFABLE
                issues = validate_buffable_shape(blob)
                if issues:
                    invalid.append(f"row{i}:{pname}:{issues}")
                else:
                    parsed = parse_buffable_speed_blob(pname, blob)
                    assert parsed["dump_type"] == DUMP_TYPE_BUFFABLE
            else:
                assert dtype == DUMP_TYPE_MULTIPLE
                issues = validate_multiple_shape(blob)
                if issues:
                    invalid.append(f"row{i}:{pname}:{issues}")
                else:
                    parsed = parse_multiple_speed_blob(pname, blob)
                    assert parsed["cycle_ref_type"] == DUMP_TYPE_BUFFABLE
                    assert parsed["multiplier"] == 4

    assert counts == {
        "BeltSpeed": 1,
        "ConveyorSpeed": 4,
        "SpaceConveyorSpeed": 3,
        "JumpSpeed": 2,
    }
    assert mismatches == []
    assert invalid == []


def test_space_conveyor_quarter_second_per_tile() -> None:
    rows = _load_rows()
    seen = 0
    for row in rows:
        blob = (row.get("simulation_parameters") or {}).get("SpaceConveyorSpeed")
        if not isinstance(blob, dict):
            continue
        parsed = parse_buffable_speed_blob("SpaceConveyorSpeed", blob)
        assert parsed["base_speed"] == "QuarterSecondPerTile"
        assert parsed["steps_per_tick"] == 100800
        seen += 1
    assert seen == 3
