"""PR-16: golden fixture must expose at least one inner routeable L4 source."""

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
from shapez2_factory.application.asteroid_lab.experiments.golden_l4_capacity_metrics import (
    compute_golden_l4_capacity_metrics,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_valid_baseline import (
    CANONICAL_BUDGET_MS,
    CANONICAL_SPEED_TIER,
    CANONICAL_THROUGHPUT_TARGET_PERCENT,
    assert_master_valid_eval_result,
    assert_master_valid_route_plan,
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


@pytest.mark.skipif(not _fixtures_ready(), reason="golden fixture files missing")
def test_golden_solver_exposes_inner_routeable_group_source() -> None:
    artifacts = run_golden_solver(
        copy_text=load_empty_copy(),
        game_data_rules=load_game_data_rules(),
        genetic_sample_seeds=load_genetic_sample_seeds(),
        config=GoldenSolverConfig(
            throughput_target_percent=CANONICAL_THROUGHPUT_TARGET_PERCENT,
            budget_ms=CANONICAL_BUDGET_MS,
            speed_tier=CANONICAL_SPEED_TIER,
        ),
    )
    metrics = compute_golden_l4_capacity_metrics(artifacts)

    assert metrics.inner_routeable_group_count >= 1
    assert metrics.routeable_gap_to_target_b < 55
    assert metrics.routeable_group_count > metrics.rim_group_count

    assert_master_valid_route_plan(artifacts.route_plan)
    oracle = build_golden_oracle(decode_copy_string(load_golden_copy()).root)
    eval_result = evaluate_against_golden(artifacts, oracle)
    assert_master_valid_eval_result(eval_result)
