"""Solver Runtime A→M pipeline unit tests (PR7)."""

from __future__ import annotations

from pathlib import Path

from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.optimization.gene_template_loader import load_gene_templates_from_json
from django_apps.asteroid_lab.optimization.loaded_snapshot import LoadedReconstructionSnapshot
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_loaded_snapshot,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.services.solver_runtime_pipeline import run_solver_runtime_pipeline

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "gene_templates"


def _minimal_gene_templates() -> tuple:
    return load_gene_templates_from_json(_FIXTURE_DIR / "minimal_extractor_e.json")


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
        gene_templates=_minimal_gene_templates(),
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
    templates = _minimal_gene_templates()

    r1 = run_solver_runtime_pipeline(loaded=loaded, gene_templates=templates)
    r2 = run_solver_runtime_pipeline(loaded=loaded, gene_templates=templates)

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
        f
        for f in r1.replay_frames
        if f.event_type == OptimizationReplayEventType.VALIDATION_COMPLETED
    )
    metrics = validation_frame.metrics
    assert "first_issue_detail" in metrics
    if metrics.get("first_issue_code"):
        detail = metrics["first_issue_detail"]
        assert isinstance(detail, dict)
        assert detail["issue_code"] == metrics["first_issue_code"]


_JS_RECOGNISED_CELL_KINDS = frozenset(
    {
        "space_belt",
        "space_pipe",
        "shape_miner",
        "fluid_miner",
        "shape_miner_extension",
        "fluid_miner_extension",
        "asteroid_shape_field",
        "asteroid_fluid_field",
    }
)


def test_pipeline_overlay_cells_have_js_recognised_cell_kinds() -> None:
    """ROUTE_MATERIALIZED and VALIDATION_COMPLETED overlays must only use JS-known cell kinds."""
    loaded = _pipeline_loaded_snapshot()
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_minimal_gene_templates(),
        run_key="overlay_kinds_check",
    )

    for frame in result.replay_frames:
        if frame.event_type not in (
            OptimizationReplayEventType.ROUTE_MATERIALIZED,
            OptimizationReplayEventType.VALIDATION_COMPLETED,
        ):
            continue
        for cell in frame.overlay_cells:
            ck = cell.get("cell_kind", "")
            assert ck in _JS_RECOGNISED_CELL_KINDS or ck == "", (
                f"Unknown cell_kind {ck!r} in {frame.event_type} overlay — "
                "add it to toneForFullMapCell in JS"
            )
        # sentinel must never appear
        for cell in frame.overlay_cells:
            assert cell.get("cell_kind") != "route_materialized"


def test_pipeline_validation_overlay_differs_from_base_cells() -> None:
    """If any route was committed, final overlay must contain cells not in visible_cells."""
    loaded = _pipeline_loaded_snapshot()
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_minimal_gene_templates(),
        run_key="overlay_diff_check",
    )

    validation_frame = next(
        f
        for f in result.replay_frames
        if f.event_type == OptimizationReplayEventType.VALIDATION_COMPLETED
    )
    input_frame = next(
        f
        for f in result.replay_frames
        if f.event_type == OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED
    )

    if result.solver_summary.get("confirmed_count", 0) == 0:
        return  # no commits — diff not required

    base_coords = frozenset((c["server_x"], c["server_y"]) for c in input_frame.visible_cells)
    overlay_coords = frozenset(
        (c["server_x"], c["server_y"]) for c in validation_frame.overlay_cells
    )
    # overlay must have cells not in the base asteroid field (i.e. belt/miner cells)
    assert (
        overlay_coords - base_coords
    ), "VALIDATION_COMPLETED overlay has no new cells beyond the base asteroid field"


def test_runtime_pipeline_emits_only_known_replay_event_types() -> None:
    """All event_type values in recorder output must be valid OptimizationReplayEventType."""
    loaded = _pipeline_loaded_snapshot()
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_minimal_gene_templates(),
        run_key="event_types_check",
    )
    known = frozenset(OptimizationReplayEventType)
    for frame in result.replay_frames:
        assert (
            frame.event_type in known
        ), f"Unknown event_type {frame.event_type!r} emitted by runtime pipeline"


def test_solver_runtime_emits_result_layout_after_validation() -> None:
    """Pipeline must emit a RESULT_LAYOUT frame as the last replay event."""
    loaded = _pipeline_loaded_snapshot()
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_minimal_gene_templates(),
        run_key="result_layout_check",
    )
    assert result.replay_frames, "replay_frames must not be empty"
    last = result.replay_frames[-1]
    assert (
        last.event_type == OptimizationReplayEventType.RESULT_LAYOUT
    ), f"Last frame must be RESULT_LAYOUT, got {last.event_type!r}"
    assert "validation_passed" in last.metrics


def test_result_layout_has_full_cells_not_overlay_only() -> None:
    """RESULT_LAYOUT frame must carry reconstruction cells in visible_cells
    so the unified adapter can populate map_view.full_cells (not overlay only)."""
    loaded = _pipeline_loaded_snapshot()
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_minimal_gene_templates(),
        run_key="result_layout_cells_check",
    )
    result_frame = next(
        f for f in result.replay_frames if f.event_type == OptimizationReplayEventType.RESULT_LAYOUT
    )
    assert (
        len(result_frame.visible_cells) >= 1
    ), "RESULT_LAYOUT frame must include reconstruction visible_cells for full_cells projection"
    assert any("server_x" in c for c in result_frame.visible_cells)


def test_route_committed_metrics_include_path_diagnostics() -> None:
    from django_apps.asteroid_lab.optimization.candidate_selector import (
        SelectedCandidatePlan,
    )
    from django_apps.asteroid_lab.optimization.commit_best_candidates import (
        commit_selected_candidates,
    )
    from django_apps.asteroid_lab.services.solver_runtime_pipeline import (
        _route_committed_metrics,
    )
    from tests.unit.asteroid_lab.test_incremental_commit import (
        _open_void_inp,
        _shape_candidate,
    )

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
