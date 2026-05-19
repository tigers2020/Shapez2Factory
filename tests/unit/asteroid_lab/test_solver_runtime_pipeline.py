"""Solver Runtime A→M pipeline unit tests (PR7)."""

from __future__ import annotations

from pathlib import Path

from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.optimization.loaded_snapshot import LoadedReconstructionSnapshot
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_loaded_snapshot,
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
    """Single rim mineable cell at server (0, 0) with void goals along +x."""

    return LoadedReconstructionSnapshot(
        cells=(_cell(1, 0, cell_kind="shape_miner_extension", server_x=0, server_y=0),),
        server_xy_params=(1, 0),
    )


def test_pipeline_runs_end_to_end_without_orm() -> None:
    loaded = _pipeline_loaded_snapshot()
    inp = optimization_input_from_loaded_snapshot(loaded)
    assert len(inp.rim_cells) >= 1

    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_template_path=_FIXTURE_DIR / "minimal_extractor_e.json",
        run_key="unit",
    )

    assert result.run_key == "unit"
    assert isinstance(result.solver_summary["validation_passed"], bool)
    assert "confirmed_count" in result.solver_summary
    assert "issue_details" in result.solver_summary
    assert isinstance(result.solver_summary["issue_details"], list)
    assert len(result.replay_frames) >= 5


def test_pipeline_replay_event_sequence_is_deterministic() -> None:
    loaded = _pipeline_loaded_snapshot()
    path = _FIXTURE_DIR / "minimal_extractor_e.json"

    r1 = run_solver_runtime_pipeline(loaded=loaded, gene_template_path=path)
    r2 = run_solver_runtime_pipeline(loaded=loaded, gene_template_path=path)

    seq1 = [f.event_type for f in r1.replay_frames]
    seq2 = [f.event_type for f in r2.replay_frames]
    assert seq1 == seq2

    required = {
        OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
        OptimizationReplayEventType.CAPACITY_PLAN_CREATED,
        OptimizationReplayEventType.ROUTE_GOAL_GENERATED,
        OptimizationReplayEventType.CANDIDATE_POOL_COMPLETED,
        OptimizationReplayEventType.CANDIDATE_SELECTION_COMPLETED,
        OptimizationReplayEventType.ROUTE_MATERIALIZED,
        OptimizationReplayEventType.VALIDATION_COMPLETED,
    }
    assert required.issubset(set(seq1))

    input_frame = next(
        f
        for f in r1.replay_frames
        if f.event_type == OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED
    )
    assert len(input_frame.visible_cells) >= 1
    assert "server_x" in input_frame.visible_cells[0]

    validation_frame = next(
        f for f in r1.replay_frames if f.event_type == OptimizationReplayEventType.VALIDATION_COMPLETED
    )
    metrics = validation_frame.metrics
    assert "first_issue_detail" in metrics
    if metrics.get("first_issue_code"):
        detail = metrics["first_issue_detail"]
        assert isinstance(detail, dict)
        assert detail["issue_code"] == metrics["first_issue_code"]


def test_route_committed_metrics_include_path_diagnostics() -> None:
    from django_apps.asteroid_lab.optimization.candidate_selector import SelectedCandidatePlan
    from django_apps.asteroid_lab.optimization.commit_best_candidates import commit_selected_candidates
    from django_apps.asteroid_lab.services.solver_runtime_pipeline import _route_committed_metrics
    from tests.unit.asteroid_lab.test_incremental_commit import _open_void_inp, _shape_candidate

    inp = _open_void_inp()
    candidate = _shape_candidate(candidate_id="a:1")
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1",))
    commit = commit_selected_candidates(plan, {candidate.candidate_id: candidate}, inp=inp)
    assert commit.confirmed
    placement = commit.confirmed[0]
    metrics = _route_committed_metrics(placement, {candidate.candidate_id: candidate})
    assert metrics["candidate_id"] == "a:1"
    assert metrics["route_reservation_id"] == placement.reservation.reservation_id
    assert metrics["path_len"] == metrics["reserved_cell_count"]
    assert metrics["path_contains_output_stub"] is True
    assert metrics["output_stub"] == list(candidate.fixed_output_transport)
