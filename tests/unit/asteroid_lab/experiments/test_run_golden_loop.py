"""PR-5: golden loop script output and boundary tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest import mock

import pytest

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_eval import (
    GoldenEvalResult,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures import (
    golden_fixture_dir,
)

_REPO = Path(__file__).resolve().parents[4]
_SCRIPTS = _REPO / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

_FIXTURE_ROOT = golden_fixture_dir()


def _load_loop_module():
    spec = importlib.util.spec_from_file_location(
        "run_golden_loop",
        _SCRIPTS / "run_golden_loop.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


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


def _eval_result(
    *,
    valid: bool,
    score: float,
    diagnostics: tuple[str, ...] = (),
) -> GoldenEvalResult:
    return GoldenEvalResult(
        valid=valid,
        score=score,
        miner_count=1,
        belt_count=2,
        routed_throughput=30.0,
        anchor_f1_direct=0.1,
        anchor_f1_normalized=0.1,
        golden_belt_similarity=0.0,
        route_island_count=0,
        orphan_count=0,
        diagnostics=diagnostics,
    )


def test_run_golden_loop_write_best_copy_is_opt_in() -> None:
    source = (_SCRIPTS / "run_golden_loop.py").read_text(encoding="utf-8")
    assert "--write-best-copy" in source
    assert "write_best_copy" in source
    assert "if write_best_copy" in source


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_run_golden_loop_writes_outputs(tmp_path: Path) -> None:
    loop = _load_loop_module()
    configs = (
        loop.GoldenLoopRunConfig(throughput_target_percent=70, budget_ms=60_000, speed_tier=1),
        loop.GoldenLoopRunConfig(throughput_target_percent=80, budget_ms=60_000, speed_tier=1),
        loop.GoldenLoopRunConfig(throughput_target_percent=90, budget_ms=60_000, speed_tier=1),
    )
    eval_results = [
        _eval_result(valid=False, score=100.0, diagnostics=("l5_failed_sources:1",)),
        _eval_result(valid=True, score=500.0),
        _eval_result(valid=True, score=800.0),
    ]
    fixed_now = datetime(2026, 6, 9, 12, 0, 0, tzinfo=UTC)

    with (
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run.run_golden_solver",
            return_value=mock.Mock(),
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_eval.evaluate_against_golden",
            side_effect=eval_results,
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures.load_empty_copy",
            return_value="empty$",
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures.load_golden_copy",
            return_value="golden$",
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures.load_game_data_rules",
            return_value=mock.Mock(),
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures.load_genetic_sample_seeds",
            return_value=mock.Mock(),
        ),
        mock.patch(
            "shapez2_factory.domain.asteroid_lab.copy_decode.decode_copy_string",
            return_value=mock.Mock(root={"mock": True}),
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_loader.build_golden_oracle",
            return_value=mock.Mock(),
        ),
    ):
        summary = loop.run_golden_loop(
            out_dir=tmp_path,
            configs=configs,
            now_fn=lambda: fixed_now,
        )

    runs_path = tmp_path / "runs.jsonl"
    best_path = tmp_path / "best_config.json"
    diag_path = tmp_path / "diagnostics.json"
    assert runs_path.is_file()
    assert best_path.is_file()
    assert diag_path.is_file()
    assert summary["run_count"] == 3
    assert summary["best_valid"] is True
    assert summary["best_score"] == 800.0

    lines = runs_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    for line in lines:
        json.loads(line)

    best = json.loads(best_path.read_text(encoding="utf-8"))
    assert best["config"]["throughput_target_percent"] == 90
    assert best["result"]["score"] == 800.0

    diagnostics = json.loads(diag_path.read_text(encoding="utf-8"))
    assert diagnostics["failure_patterns"]["l5_failed_sources:1"] == 1
    assert diagnostics["run_count"] == 3
    assert diagnostics["best_valid"] is True
    assert diagnostics["best_score"] == 800.0
    assert not (tmp_path / "best_result.shapez.txt").exists()


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_run_golden_loop_writes_best_copy_when_requested(tmp_path: Path) -> None:
    loop = _load_loop_module()
    configs = (
        loop.GoldenLoopRunConfig(throughput_target_percent=80, budget_ms=60_000, speed_tier=1),
    )
    eval_results = [_eval_result(valid=True, score=500.0)]
    fake_artifacts = mock.Mock(name="artifacts")

    with (
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run.run_golden_solver",
            return_value=fake_artifacts,
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_eval.evaluate_against_golden",
            side_effect=eval_results,
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures.load_empty_copy",
            return_value="empty$",
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures.load_golden_copy",
            return_value="golden$",
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures.load_game_data_rules",
            return_value=mock.Mock(),
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures.load_genetic_sample_seeds",
            return_value=mock.Mock(),
        ),
        mock.patch(
            "shapez2_factory.domain.asteroid_lab.copy_decode.decode_copy_string",
            return_value=mock.Mock(root={"mock": True}),
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_loader.build_golden_oracle",
            return_value=mock.Mock(),
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_assembler.encode_candidate_copy_string",
            return_value="SHAPEZ2-4-test$",
        ) as encode_mock,
    ):
        summary = loop.run_golden_loop(
            out_dir=tmp_path,
            configs=configs,
            write_best_copy=True,
        )

    best_copy_path = tmp_path / "best_result.shapez.txt"
    assert best_copy_path.is_file()
    assert best_copy_path.read_text(encoding="utf-8") == "SHAPEZ2-4-test$\n"
    assert summary["best_copy_path"] == str(best_copy_path)
    encode_mock.assert_called_once_with(artifacts=fake_artifacts, empty_copy="empty$")


def test_run_golden_loop_db_gene_seeds_writes_snapshot(tmp_path: Path) -> None:
    loop = _load_loop_module()
    configs = (
        loop.GoldenLoopRunConfig(throughput_target_percent=80, budget_ms=60_000, speed_tier=1),
    )
    fake_seeds = mock.Mock(entries=(mock.Mock(), mock.Mock()))
    seed_payload = {
        "schema_version": "genetic_sample_seed_v1",
        "entries": [{"gene_id": "miner_seed_m0e_01"}],
        "provenance_hash": "abc",
    }

    with (
        mock.patch.object(
            loop,
            "_load_genetic_sample_seeds_for_loop",
            return_value=(fake_seeds, seed_payload),
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run.run_golden_solver",
            return_value=mock.Mock(),
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_eval.evaluate_against_golden",
            return_value=_eval_result(valid=True, score=100.0),
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures.load_empty_copy",
            return_value="empty$",
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures.load_golden_copy",
            return_value="golden$",
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures.load_game_data_rules",
            return_value=mock.Mock(),
        ),
        mock.patch(
            "shapez2_factory.domain.asteroid_lab.copy_decode.decode_copy_string",
            return_value=mock.Mock(root={"mock": True}),
        ),
        mock.patch(
            "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_loader.build_golden_oracle",
            return_value=mock.Mock(),
        ),
    ):
        summary = loop.run_golden_loop(
            out_dir=tmp_path,
            configs=configs,
            gene_seeds_source="db",
            gene_seeds_db_scope="admin",
        )

    snapshot_path = tmp_path / "genetic_sample_seeds.json"
    assert snapshot_path.is_file()
    diagnostics = json.loads((tmp_path / "diagnostics.json").read_text(encoding="utf-8"))
    assert diagnostics["gene_seeds_source"] == "db"
    assert diagnostics["gene_seeds_entry_count"] == 2
    assert summary["best_valid"] is True
