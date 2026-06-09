"""Golden smoke regression for PR-9 L5 capacity accounting fix."""

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
from shapez2_factory.application.asteroid_lab.experiments.golden_valid_baseline import (
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


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_golden_capacity_overflow_reduced_after_lane_load_mapping() -> None:
    oracle = build_golden_oracle(decode_copy_string(load_golden_copy()).root)
    artifacts = run_golden_solver(
        copy_text=load_empty_copy(),
        game_data_rules=load_game_data_rules(),
        genetic_sample_seeds=load_genetic_sample_seeds(),
        config=GoldenSolverConfig(budget_ms=60_000),
    )
    assert_master_valid_route_plan(artifacts.route_plan)
    result = evaluate_against_golden(artifacts, oracle)
    assert_master_valid_eval_result(result)
