"""Solver runtime performance budgets and replay isolation."""

from __future__ import annotations

from pathlib import Path

from django_apps.asteroid_lab.optimization.candidate_generator import default_generation_config
from django_apps.asteroid_lab.optimization.loaded_snapshot import LoadedReconstructionSnapshot
from django_apps.asteroid_lab.replay.solver_runtime_replay_recorder import (
    SolverRuntimeReplayRecorder,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.services.solver_runtime_pipeline import run_solver_runtime_pipeline

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "gene_templates"


def _cell(
    x: int,
    y: int,
    *,
    cell_kind: str = "shape_miner_extension",
    server_x: int | None = None,
    server_y: int | None = None,
) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind=cell_kind,
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
        server_x=server_x,
        server_y=server_y,
    )


def _pipeline_loaded_snapshot() -> LoadedReconstructionSnapshot:
    return LoadedReconstructionSnapshot(
        cells=(_cell(1, 0, cell_kind="shape_miner_extension", server_x=0, server_y=0),),
        server_xy_params=(1, 0),
    )


def _aggressive_config():
    return default_generation_config(max_candidates=40, route_probe_max_expansions=128)


def _load_minimal_genes():
    from django_apps.asteroid_lab.optimization.gene_template_loader import (
        load_gene_templates_from_json,
    )

    return load_gene_templates_from_json(_FIXTURE_DIR / "minimal_extractor_e.json")


def test_simple_runtime_completes_within_budget_replay_off() -> None:
    loaded = _pipeline_loaded_snapshot()
    config = _aggressive_config()
    genes = _load_minimal_genes()

    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=genes,
        generation_config=config,
        recorder=None,
    )

    timing = result.solver_summary.get("timing") or {}
    assert timing.get("total_ms", 0) < 3000.0
    probe_count = int(timing.get("route_probe_count", 0))
    max_exp = config.route_probe_max_expansions
    probe_cap = (config.max_candidates or 0) * config.probe_budget_factor
    assert probe_count <= probe_cap
    assert int(timing.get("route_probe_expanded_nodes_total", 0)) <= probe_count * max_exp


def test_replay_does_not_change_commit_outcome() -> None:
    loaded = _pipeline_loaded_snapshot()
    config = _aggressive_config()
    genes = _load_minimal_genes()

    off = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=genes,
        generation_config=config,
        recorder=None,
    )
    recorder = SolverRuntimeReplayRecorder(
        loaded,
        loaded.server_xy_params or (1, 0),
        gene_templates_by_id={g.gene_id: g for g in genes},
    )
    on = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=genes,
        generation_config=config,
        recorder=recorder,
    )

    assert [c.candidate_id for c in off.commit.confirmed] == [
        c.candidate_id for c in on.commit.confirmed
    ]
    assert off.commit.skipped_candidate_ids == on.commit.skipped_candidate_ids
    assert off.solver_summary.get("confirmed_count") == on.solver_summary.get("confirmed_count")
