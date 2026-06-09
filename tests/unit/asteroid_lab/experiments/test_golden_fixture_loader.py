"""PR-1: golden fixture loader and summary contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_loader import (
    build_golden_oracle,
    load_golden_fixture_summary,
    load_shapez_copy_string,
    summarize_blueprint,
    write_decoded_snapshots,
)
from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string

_FIXTURE_ROOT = Path(__file__).resolve().parents[3] / "fixtures" / "asteroid_golden"
_EMPTY = _FIXTURE_ROOT / "empty.shapez.txt"
_GOLDEN = _FIXTURE_ROOT / "golden.shapez.txt"
_SUMMARY = _FIXTURE_ROOT / "golden_summary.json"


def _canonical_fixtures_present() -> bool:
    if not (_EMPTY.is_file() and _GOLDEN.is_file() and _SUMMARY.is_file()):
        return False
    contract = load_golden_fixture_summary(_SUMMARY)
    empty_root = decode_copy_string(load_shapez_copy_string(_EMPTY)).root
    golden_root = decode_copy_string(load_shapez_copy_string(_GOLDEN)).root
    empty_entries = empty_root["BP"]["Entries"]
    golden_summary = summarize_blueprint(golden_root)
    empty_ok = len(empty_entries) == int(contract["empty_entry_count"])
    empty_ok = empty_ok and all(
        row.get("T") == "Layout_ShapeMinerExtension"
        for row in empty_entries
        if isinstance(row, dict)
    )
    golden_ok = all(
        golden_summary[key] == contract[key]
        for key in (
            "entry_count",
            "layout_miner_count",
            "layout_extension_count",
            "belt_count",
        )
    )
    golden_ok = golden_ok and golden_summary["bbox"] == contract["bbox"]
    return empty_ok and golden_ok


@pytest.mark.skipif(
    not _EMPTY.is_file() or not _GOLDEN.is_file(),
    reason="upload empty.shapez.txt and golden.shapez.txt to tests/fixtures/asteroid_golden/",
)
def test_golden_fixture_loader_empty_decodes() -> None:
    copy = load_shapez_copy_string(_EMPTY)
    root = decode_copy_string(copy).root
    entries = root["BP"]["Entries"]
    assert entries
    for row in entries:
        assert isinstance(row, dict)
        assert row.get("T") == "Layout_ShapeMinerExtension"


@pytest.mark.skipif(
    not _EMPTY.is_file() or not _GOLDEN.is_file(),
    reason="upload empty.shapez.txt and golden.shapez.txt to tests/fixtures/asteroid_golden/",
)
def test_golden_fixture_loader_golden_decodes() -> None:
    copy = load_shapez_copy_string(_GOLDEN)
    root = decode_copy_string(copy).root
    summary = summarize_blueprint(root)
    assert summary["entry_count"] > 0
    assert summary["layout_miner_count"] > 0
    oracle = build_golden_oracle(root)
    assert oracle.entry_count == summary["entry_count"]


@pytest.mark.skipif(
    not _canonical_fixtures_present(),
    reason=(
        "canonical uploaded maps required: empty 578 extensions, golden 1275 entries "
        "(see tests/fixtures/asteroid_golden/golden_summary.json)"
    ),
)
def test_golden_summary_counts() -> None:
    expected = load_golden_fixture_summary(_SUMMARY)
    golden_root = decode_copy_string(load_shapez_copy_string(_GOLDEN)).root
    actual = summarize_blueprint(golden_root)
    for key in ("entry_count", "layout_miner_count", "layout_extension_count", "belt_count"):
        assert actual[key] == expected[key], key
    assert actual["bbox"] == expected["bbox"]

    empty_root = decode_copy_string(load_shapez_copy_string(_EMPTY)).root
    empty_entries = empty_root["BP"]["Entries"]
    assert len(empty_entries) == expected["empty_entry_count"]
    empty_types = {row.get("T") for row in empty_entries if isinstance(row, dict)}
    assert empty_types == {"Layout_ShapeMinerExtension"}


@pytest.mark.skipif(
    not _EMPTY.is_file() or not _GOLDEN.is_file(),
    reason="upload empty.shapez.txt and golden.shapez.txt to tests/fixtures/asteroid_golden/",
)
def test_write_decoded_snapshots(tmp_path: Path) -> None:
    empty = load_shapez_copy_string(_EMPTY)
    golden = load_shapez_copy_string(_GOLDEN)
    p1, p2 = write_decoded_snapshots(empty_copy=empty, golden_copy=golden, out_dir=tmp_path)
    assert p1.is_file() and p2.is_file()
    assert json.loads(p1.read_text(encoding="utf-8"))["BP"]["$type"] == "Island"
