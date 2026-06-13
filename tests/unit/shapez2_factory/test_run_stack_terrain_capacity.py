"""CLI run_stack terrain upper bound uses mining extraction, not EVTC connector caps."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from shapez2_factory.adapters.asteroid_lab.json_snapshot_rules import (
    JsonSnapshotGameDataRulesAdapter,
)
from shapez2_factory.application.asteroid_lab.run_stack import RunStackUseCase

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "asteroid_lab"
    / "game_data_snapshot_min.json"
)
_COPY_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "asteroid_lab"
    / "reconstruction_required_.txt"
)


def test_run_stack_capacity_matches_mining_not_space_belt() -> None:
    rules = JsonSnapshotGameDataRulesAdapter.from_file(_FIXTURE)
    copy_text = _COPY_FIXTURE.read_text(encoding="utf-8").strip().splitlines()[0]

    result = RunStackUseCase(game_data_rules=rules).run(
        copy_text=copy_text,
        throughput_target_percent=100,
        budget_ms=60_000,
    )

    assert result.ok is True
    cap = result.solver_summary["reconstruction_capacity"]
    shape = cap["by_resource"]["shape"]
    platform_count = int(shape["capacity_upper_bound_platform_count"])
    max_tp = Decimal(shape["max_throughput_per_min"])
    per_cell = Decimal(shape["output_per_confirmed_cell"])

    assert per_cell == Decimal("120.0000")
    assert max_tp == per_cell * Decimal(platform_count)
    assert max_tp != Decimal("5760.0000") * Decimal(4) * Decimal(platform_count)
    l2 = next(
        item
        for item in result.solver_summary["layer_summaries"]
        if item["layer_slug"] == "layer_02_exterior_transport"
    )
    assert l2["metrics"] == {"stub": True}
