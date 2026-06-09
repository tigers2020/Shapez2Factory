"""Golden loop integration tests for L5 failed-source diagnostics."""

from __future__ import annotations

import pytest

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_eval import (
    evaluate_against_golden,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures import (
    golden_fixture_dir,
    load_empty_copy,
    load_game_data_rules,
    load_genetic_sample_seeds,
    load_golden_copy,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_loader import (
    build_golden_oracle,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run import (
    GoldenSolverConfig,
    run_golden_solver,
)
from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string

_FIXTURE_ROOT = golden_fixture_dir()


def _fixtures_ready() -> bool:
    return all(
        (_FIXTURE_ROOT / name).is_file()
        for name in (
            "empty.shapez.txt",
            "golden.shapez.txt",
            "game_data_snapshot_min.json",
            "genetic_sample_seeds.json",
        )
    )


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_golden_eval_includes_l5_failure_histogram() -> None:
    oracle = build_golden_oracle(decode_copy_string(load_golden_copy()).root)
    artifacts = run_golden_solver(
        copy_text=load_empty_copy(),
        game_data_rules=load_game_data_rules(),
        genetic_sample_seeds=load_genetic_sample_seeds(),
        config=GoldenSolverConfig(budget_ms=60_000),
    )
    result = evaluate_against_golden(artifacts, oracle)
    assert any(d.startswith("l5_failure_bucket:") for d in result.diagnostics)
    assert any(d.startswith("l5_failure_reason:") for d in result.diagnostics)
    assert "l5_failed_sources:60" in result.diagnostics


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_golden_solver_route_metrics_unchanged() -> None:
    artifacts = run_golden_solver(
        copy_text=load_empty_copy(),
        game_data_rules=load_game_data_rules(),
        genetic_sample_seeds=load_genetic_sample_seeds(),
        config=GoldenSolverConfig(budget_ms=60_000),
    )
    assert artifacts.route_plan is not None
    metrics = artifacts.route_plan.metrics
    assert metrics.source_count == 76
    assert metrics.failed_source_count == 60
    assert metrics.routed_source_count == 16
    assert len(artifacts.route_plan.failed_source_diagnostics) == 60
