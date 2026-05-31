"""Gene catalog plumbing: subprocess args, use-case signature acceptance (A3)."""

from __future__ import annotations

import inspect
from pathlib import Path

from django_apps.asteroid_lab.services.solver_subprocess_runner import (
    SolverSubprocessRequest,
    build_solver_cli_args,
)
from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import GeneticSampleSeedSnapshot
from shapez2_factory.adapters.asteroid_lab.json_snapshot_rules import (
    JsonSnapshotGameDataRulesAdapter,
)
from shapez2_factory.application.asteroid_lab.run_stack import RunStackUseCase

_FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab"
_SNAPSHOT_FIXTURE = _FIXTURE_ROOT / "game_data_snapshot_min.json"
_COPY_FIXTURE = _FIXTURE_ROOT / "reconstruction_required_.txt"

_GENETIC_SAMPLE_SEEDS_PAYLOAD = {
    "schema_version": "genetic_sample_seed_v1",
    "entries": [],
}


def test_cli_args_include_gene_catalog(tmp_path: Path) -> None:
    req = SolverSubprocessRequest(
        run_key="k1",
        copy_code="SHAPEZ2-4-x",
        game_data_snapshot={"schema_version": "game_data_snapshot_v1"},
        genetic_sample_seeds=_GENETIC_SAMPLE_SEEDS_PAYLOAD,
        artifact_root=tmp_path,
        allowed_root=tmp_path,
        timeout_seconds=5.0,
    )
    args = build_solver_cli_args(
        req,
        copy_path=tmp_path / "c.txt",
        snapshot_path=tmp_path / "s.json",
        genetic_sample_seeds_path=tmp_path / "g.json",
    )
    assert "--genetic-sample-seeds" in args
    idx = args.index("--genetic-sample-seeds")
    assert args[idx + 1] == str(tmp_path / "g.json")


def test_run_stack_accepts_gene_catalog_kwarg() -> None:
    sig = inspect.signature(RunStackUseCase.run)
    assert "genetic_sample_seeds" in sig.parameters


def test_run_stack_runs_with_gene_catalog_none_and_snapshot() -> None:
    rules = JsonSnapshotGameDataRulesAdapter.from_file(_SNAPSHOT_FIXTURE)
    copy_text = _COPY_FIXTURE.read_text(encoding="utf-8").strip().splitlines()[0]
    snapshot = GeneticSampleSeedSnapshot.from_payload(_GENETIC_SAMPLE_SEEDS_PAYLOAD)

    use_case = RunStackUseCase(game_data_rules=rules)

    result_none = use_case.run(copy_text=copy_text, genetic_sample_seeds=None)
    result_snapshot = use_case.run(copy_text=copy_text, genetic_sample_seeds=snapshot)

    assert result_none.ok is True
    assert result_snapshot.ok is True
