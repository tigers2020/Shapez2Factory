"""Tests for JSONL boundary logging (``observability/boundary_jsonl``)."""

from __future__ import annotations

import json

import pytest

from django_apps.asteroid_lab.observability.boundary_jsonl import (
    boundary_jsonl_enabled,
    emit_boundary_jsonl,
    summarize_cell_kind_transitions,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO


def _cell(x: int, y: int, *, cell_kind: str) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind=cell_kind,
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
    )


def test_emit_boundary_jsonl_respects_enable_flag(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.delenv("ASTEROID_LAB_BOUNDARY_JSONL", raising=False)
    emit_boundary_jsonl(run_id="r1", stage="s", boundary="b", data={"x": 1})
    assert not (tmp_path / "r1.jsonl").exists()

    monkeypatch.setenv("ASTEROID_LAB_BOUNDARY_JSONL", "1")
    monkeypatch.setenv("ASTEROID_LAB_BOUNDARY_JSONL_DIR", str(tmp_path))
    emit_boundary_jsonl(run_id="r1", stage="decode", boundary="decode.test", data={"n": 2})
    lines = (tmp_path / "r1.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["run_id"] == "r1"
    assert obj["stage"] == "decode"
    assert obj["boundary"] == "decode.test"
    assert obj["n"] == 2


def test_boundary_jsonl_enabled_truthy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASTEROID_LAB_BOUNDARY_JSONL", "on")
    assert boundary_jsonl_enabled() is True


def test_summarize_cell_kind_transitions() -> None:
    before = (_cell(1, 0, cell_kind="internal_void"), _cell(2, 0, cell_kind="space_belt"))
    after = (_cell(1, 0, cell_kind="asteroid_shape_field"), _cell(2, 0, cell_kind="space_belt"))
    t = summarize_cell_kind_transitions(before, after)
    assert len(t) == 1
    assert t[0]["raw_x"] == 1
    assert t[0]["raw_y"] == 0
    assert t[0]["cell_kind_before"] == "internal_void"
    assert t[0]["cell_kind_after"] == "asteroid_shape_field"
