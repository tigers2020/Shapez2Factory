"""PR-12: regression guard for master valid Golden Loop baseline."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

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
    CANONICAL_BUDGET_MS,
    CANONICAL_SPEED_TIER,
    CANONICAL_THROUGHPUT_TARGET_PERCENT,
    FROZEN_MIN_SOURCE_COUNT,
    MASTER_MIN_ROUTED_THROUGHPUT,
    assert_master_valid_diagnostics_payload,
    assert_master_valid_eval_result,
    assert_master_valid_loop_summary,
    assert_master_valid_route_plan,
)
from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string

_REPO = Path(__file__).resolve().parents[4]
_SCRIPTS = _REPO / "scripts"
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


def _load_loop_module():
    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "run_golden_loop",
        _SCRIPTS / "run_golden_loop.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_master_valid_baseline_constants_match_report() -> None:
    assert CANONICAL_THROUGHPUT_TARGET_PERCENT == 80
    assert CANONICAL_BUDGET_MS == 60_000
    assert CANONICAL_SPEED_TIER == 1
    assert FROZEN_MIN_SOURCE_COUNT == 76
    assert MASTER_MIN_ROUTED_THROUGHPUT == 37440.0


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_master_valid_baseline_solver_eval_guard() -> None:
    oracle = build_golden_oracle(decode_copy_string(load_golden_copy()).root)
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
    assert_master_valid_route_plan(artifacts.route_plan)
    result = evaluate_against_golden(artifacts, oracle)
    assert_master_valid_eval_result(result)


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_master_valid_baseline_loop_outputs_guard(tmp_path: Path) -> None:
    loop = _load_loop_module()
    summary = loop.run_golden_loop(
        out_dir=tmp_path,
        configs=(
            loop.GoldenLoopRunConfig(
                throughput_target_percent=CANONICAL_THROUGHPUT_TARGET_PERCENT,
                budget_ms=CANONICAL_BUDGET_MS,
                speed_tier=CANONICAL_SPEED_TIER,
            ),
        ),
        write_best_copy=True,
    )
    assert_master_valid_loop_summary(summary)
    assert summary["best_copy_path"] is not None
    assert Path(summary["best_copy_path"]).is_file()

    diagnostics = json.loads((tmp_path / "diagnostics.json").read_text(encoding="utf-8"))
    assert_master_valid_diagnostics_payload(diagnostics)

    best = json.loads((tmp_path / "best_config.json").read_text(encoding="utf-8"))
    assert best["result"]["valid"] is True
    assert best["result"]["miner_count"] >= FROZEN_MIN_SOURCE_COUNT
    assert best["result"]["routed_throughput"] >= MASTER_MIN_ROUTED_THROUGHPUT
    assert best["result"]["route_island_count"] == 0
    assert best["result"]["orphan_count"] == 0
