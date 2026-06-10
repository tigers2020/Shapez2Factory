"""PR-15: Golden L4 capacity / inner-fill target metrics (measurement only)."""

from __future__ import annotations

import math

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
    CANONICAL_GOLDEN_FIELD_COUNT,
    FIELD_CELLS_PER_GROUP_SET,
    MIN_INNER_FILL_RATIO,
    RIM_BASELINE_GROUP_COUNT,
    compute_golden_l4_capacity_metrics,
    format_l4_capacity_diagnostics,
    max_group_sets_for_field_count,
    min_inner_group_sets_target,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    TARGET_ROUTEABLE_FILL_RATIO,
    target_routeable_group_count_for_field,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_valid_baseline import (
    CANONICAL_BUDGET_MS,
    CANONICAL_SPEED_TIER,
    CANONICAL_THROUGHPUT_TARGET_PERCENT,
)

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


def test_max_group_sets_for_578_field_asteroid() -> None:
    assert max_group_sets_for_field_count(578) == 144
    assert min_inner_group_sets_target(68) == 55
    assert RIM_BASELINE_GROUP_COUNT + 55 == 131


def test_pure_capacity_formulas() -> None:
    inner_max = 144 - 76
    assert inner_max == 68
    target_inner = math.ceil(inner_max * MIN_INNER_FILL_RATIO)
    assert target_inner == 55
    assert 76 + target_inner == 131
    assert 76 / 144 < MIN_INNER_FILL_RATIO
    assert target_routeable_group_count_for_field(578) == math.ceil(144 * TARGET_ROUTEABLE_FILL_RATIO)
    assert target_routeable_group_count_for_field(578) == 130


@pytest.mark.skipif(not _fixtures_ready(), reason="golden fixture files missing")
def test_golden_solver_l4_capacity_metrics_expose_target_gap() -> None:
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

    assert metrics.total_field_count == CANONICAL_GOLDEN_FIELD_COUNT
    assert metrics.max_group_sets == 144
    assert metrics.rim_group_count == RIM_BASELINE_GROUP_COUNT
    target_routeable = target_routeable_group_count_for_field(CANONICAL_GOLDEN_FIELD_COUNT)
    assert metrics.routeable_group_count >= target_routeable
    assert metrics.inner_routeable_group_count >= (
        target_routeable - RIM_BASELINE_GROUP_COUNT
    )
    assert metrics.inner_max_group_sets == 68
    assert metrics.min_inner_group_sets_target == 55
    assert metrics.min_total_routeable_target == 131
    assert metrics.meets_l4_inner_target_b is False
    assert metrics.routeable_gap_to_target_b == max(
        0,
        metrics.min_total_routeable_target - metrics.routeable_group_count,
    )
    assert metrics.l4_interior_occupied_cell_count > 0
    assert metrics.l4_interior_group_set_equivalent == (
        metrics.l4_interior_occupied_cell_count // FIELD_CELLS_PER_GROUP_SET
    )

    diagnostics = format_l4_capacity_diagnostics(metrics)
    assert any(d.startswith("l4_capacity:meets_inner_target_b=False") for d in diagnostics)

    from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string

    oracle = build_golden_oracle(decode_copy_string(load_golden_copy()).root)
    eval_result = evaluate_against_golden(artifacts, oracle)
    assert any(d.startswith("l4_capacity:") for d in eval_result.diagnostics)
