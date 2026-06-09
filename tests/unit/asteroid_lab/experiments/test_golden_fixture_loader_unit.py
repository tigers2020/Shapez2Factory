"""PR-1: loader unit tests that do not require uploaded canonical fixtures."""

from __future__ import annotations

from pathlib import Path

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_loader import (
    build_golden_oracle,
    load_golden_fixture_summary,
    summarize_blueprint,
)
from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string

_LEGACY_ORIGIN = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "asteroid_golden_legacy"
    / "golden_map_origin.shapez.txt"
)
_FIXTURES = Path(__file__).resolve().parents[3] / "fixtures"
_SUMMARY = _FIXTURES / "asteroid_golden" / "golden_summary.json"


def test_golden_summary_contract_file_has_required_keys() -> None:
    summary = load_golden_fixture_summary(_SUMMARY)
    for key in (
        "entry_count",
        "layout_miner_count",
        "layout_extension_count",
        "belt_count",
        "bbox",
        "empty_entry_count",
    ):
        assert key in summary


def test_summarize_blueprint_on_legacy_origin_smoke() -> None:
    assert _LEGACY_ORIGIN.is_file(), f"missing legacy smoke fixture: {_LEGACY_ORIGIN}"
    line = _LEGACY_ORIGIN.read_text(encoding="utf-8").strip().removesuffix("$")
    root = decode_copy_string(line).root
    summary = summarize_blueprint(root)
    assert summary["entry_count"] > 0
    assert summary["layout_extension_count"] == summary["entry_count"]
    oracle = build_golden_oracle(root)
    assert oracle.belt_count == 0
