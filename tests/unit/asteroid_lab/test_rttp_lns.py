"""RTTP local LNS — RTTP-G7 (PR-5)."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from types import SimpleNamespace

import django_apps.asteroid_lab.optimization.validation.final_validation as final_validation
from django_apps.asteroid_lab.optimization.commit import local_lns
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflict,
    CommitConflictReason,
    CommitResult,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome


def _module_import_names(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[-1] if node.level else node.module.split(".")[-1])
    return names


def test_lns_only_runs_after_commit_failure() -> None:
    """Validation stays read-only; repair lives in commit/LNS modules only."""

    source = inspect.getsource(final_validation)
    assert "local_lns" not in source
    assert "run_local_lns" not in source
    assert "repair" not in source.lower()

    module_file = Path(final_validation.__file__)
    assert module_file is not None
    imported = _module_import_names(module_file)
    repair_modules = {"local_lns", "candidate_generator", "greedy_regret"}
    assert imported.isdisjoint(repair_modules)
    assert "run_local_lns" not in source

    assert "validate_final_layout" in final_validation.__all__


def _candidate(candidate_id: str, *, anchor: tuple[int, int]) -> SimpleNamespace:
    return SimpleNamespace(
        candidate_id=candidate_id,
        anchor_coord=anchor,
        pattern=object(),
        occupied_cells=frozenset({anchor}),
        output_stub=(anchor[0], anchor[1] + 1),
        output_dir="N",
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=1,
        route_probe_cost=1,
        reachable=True,
    )


def test_local_lns_refreshes_candidates_by_id_on_conflict_free_retry_without_commit_gain(
    monkeypatch,
) -> None:
    keep = _candidate("keep", anchor=(10, 10))
    conflicted = _candidate("conflict", anchor=(0, 0))
    regenerated = _candidate("regen", anchor=(0, 0))
    candidates_by_id = {
        keep.candidate_id: keep,
        conflicted.candidate_id: conflicted,
    }
    commit_result = CommitResult(
        committed_ids=(keep.candidate_id, conflicted.candidate_id),
        reserved_route_cells=frozenset(),
        domain_version=2,
        conflicts=(
            CommitConflict(
                candidate_id=conflicted.candidate_id,
                reason=CommitConflictReason.REPROBE_FAILED,
            ),
        ),
    )

    monkeypatch.setattr(
        local_lns,
        "generate_candidates",
        lambda *_args, **_kwargs: SimpleNamespace(normal_candidates=(regenerated,)),
    )
    monkeypatch.setattr(
        local_lns,
        "select_genome",
        lambda pool, *_args, **_kwargs: PlacementGenome(
            commit_order=tuple(candidate.candidate_id for candidate in pool)
        ),
    )
    monkeypatch.setattr(local_lns, "initial_commit_domain", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(
        local_lns,
        "incremental_commit",
        lambda *_args, **_kwargs: CommitResult(
            committed_ids=(keep.candidate_id,),
            reserved_route_cells=frozenset(),
            domain_version=1,
            conflicts=(),
        ),
    )

    retry_genome, retry_result = local_lns.run_local_lns(
        SimpleNamespace(),
        SimpleNamespace(),
        PlacementGenome(commit_order=(keep.candidate_id, conflicted.candidate_id)),
        candidates_by_id,
        commit_result,
    )

    assert retry_genome.commit_order == (keep.candidate_id, regenerated.candidate_id)
    assert retry_result.committed_ids == (keep.candidate_id,)
    assert candidates_by_id == {
        keep.candidate_id: keep,
        regenerated.candidate_id: regenerated,
    }
