"""Unit tests for SolverRuntimeReplayRecorder (Phase 9F/9G contracts).

Tests focus on:
- Frame ordering and event_type sequence
- Phase assignments
- map_view renderability
- Frame index monotonicity
- Source immutability (recorder must not mutate loaded snapshot)
"""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidate_dtos import CandidateGenerationResult
from django_apps.asteroid_lab.optimization.candidate_selector import SelectedCandidatePlan
from django_apps.asteroid_lab.optimization.capacity_planner import CapacityPlan
from django_apps.asteroid_lab.optimization.commit_best_candidates import IncrementalCommitResult
from django_apps.asteroid_lab.optimization.input_contracts import (
    ValidationResult,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.loaded_snapshot import LoadedReconstructionSnapshot
from django_apps.asteroid_lab.optimization.materialization_dtos import (
    MaterializedLayoutCells,
    RouteMaterializationResult,
)
from django_apps.asteroid_lab.optimization.route_goal_planner import PlannedRouteGoals
from django_apps.asteroid_lab.replay.solver_runtime_unified_recorder import (
    SolverRuntimeReplayRecorder,
)
from django_apps.asteroid_lab.replay.unified_dtos import replay_map_view_is_renderable
from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.services.dto import DecodedCellDTO

_SERVER_XY_PARAMS: tuple[int, int] = (0, 0)


def _minimal_loaded() -> LoadedReconstructionSnapshot:
    cells = (
        DecodedCellDTO(
            x=1,
            y=0,
            layer=None,
            rotation=0,
            tile_type="Layout_ProMiner",
            cell_kind="miner",
            transport_kind="none",
            has_nested_blueprint=False,
            nested_entry_count=0,
            nested_type_counts_json={},
            raw_entry_json={},
            server_x=1,
            server_y=0,
        ),
    )
    return LoadedReconstructionSnapshot(
        cells=cells,
        server_xy_params=_SERVER_XY_PARAMS,
    )


def _minimal_capacity() -> CapacityPlan:
    return CapacityPlan(
        mineable_cell_count=3,
        estimated_max_samples=1,
        estimated_shape_platforms=12,
        estimated_fluid_platforms=0,
        shape_goal_count=1,
        fluid_goal_count=0,
        avg_gene_footprint=5,
    )


def _full_recorder_run() -> SolverRuntimeReplayRecorder:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    inp = greenfield_optimization_input()
    capacity = _minimal_capacity()
    planned = PlannedRouteGoals(goals=frozenset(), capacity_plan=capacity)
    pool = CandidateGenerationResult(normal_candidates=(), rejected_candidates=())
    plan = SelectedCandidatePlan(ordered_candidate_ids=())
    commit = IncrementalCommitResult(
        confirmed=(), skipped_candidate_ids=(), goal_assigned_platforms={}
    )
    materialization = RouteMaterializationResult(
        layout=MaterializedLayoutCells(cells=()), failure_reason=None
    )
    validation = ValidationResult(passed=True, issues=())
    summary: dict = {"confirmed_count": 0, "issue_codes": [], "validation_passed": True}

    rec.record_optimization_input_loaded(inp)
    rec.record_capacity_plan_created(capacity)
    rec.record_route_goals_generated(planned)
    rec.record_candidate_pool_completed(pool)
    rec.record_candidate_selection_completed(plan)
    rec.record_route_committed(commit)
    rec.record_route_materialized(materialization)
    rec.record_validation_completed(validation)
    rec.record_result_layout(
        commit=commit,
        materialization=materialization,
        validation=validation,
        solver_summary=summary,
    )
    return rec


def test_recorder_produces_nine_frames_for_full_pipeline() -> None:
    rec = _full_recorder_run()
    assert len(rec.build_frames()) == 9


def test_recorder_last_frame_is_result_layout() -> None:
    rec = _full_recorder_run()
    frames = rec.build_frames()
    assert frames[-1].event_type == ReplayEventType.RESULT_LAYOUT
    assert frames[-1].phase == ReplayPhase.RESULT


def test_recorder_first_frame_is_optimization_input_loaded() -> None:
    rec = _full_recorder_run()
    frames = rec.build_frames()
    assert frames[0].event_type == ReplayEventType.OPTIMIZATION_INPUT_LOADED


def test_recorder_frame_index_is_monotonically_increasing() -> None:
    rec = _full_recorder_run()
    indices = [f.frame_index for f in rec.build_frames()]
    assert indices == list(range(len(indices)))


def test_recorder_required_solver_event_types_present() -> None:
    rec = _full_recorder_run()
    event_types = {f.event_type for f in rec.build_frames()}
    required = {
        ReplayEventType.OPTIMIZATION_INPUT_LOADED,
        ReplayEventType.CAPACITY_PLAN_CREATED,
        ReplayEventType.ROUTE_GOAL_GENERATED,
        ReplayEventType.CANDIDATE_POOL_COMPLETED,
        ReplayEventType.CANDIDATE_SELECTION_COMPLETED,
        ReplayEventType.ROUTE_COMMITTED,
        ReplayEventType.ROUTE_MATERIALIZED,
        ReplayEventType.VALIDATION_COMPLETED,
        ReplayEventType.RESULT_LAYOUT,
    }
    for evt in required:
        assert evt in event_types, f"Missing event type: {evt}"


def test_recorder_frames_are_renderable_when_loaded_has_cells() -> None:
    rec = _full_recorder_run()
    for frame in rec.build_frames():
        assert replay_map_view_is_renderable(frame.map_view), (
            f"Frame {frame.event_type} is not renderable"
        )


def test_recorder_result_layout_inspector_has_required_keys() -> None:
    rec = _full_recorder_run()
    result_frame = rec.build_frames()[-1]
    inspector = dict(result_frame.inspector)
    assert "confirmed_count" in inspector
    assert "validation_passed" in inspector
    assert "issue_codes" in inspector
    assert "materialized_cell_count" in inspector


def test_recorder_validation_failed_uses_correct_event_type() -> None:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    validation = ValidationResult(passed=False, issues=())
    rec.record_validation_completed(validation)
    frames = rec.build_frames()
    assert frames[0].event_type == ReplayEventType.VALIDATION_FAILED


def test_recorder_does_not_mutate_loaded_snapshot() -> None:
    loaded = _minimal_loaded()
    original_cells = loaded.cells
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    inp = greenfield_optimization_input()
    rec.record_optimization_input_loaded(inp)
    assert loaded.cells is original_cells


def test_recorder_build_frames_is_idempotent() -> None:
    rec = _full_recorder_run()
    frames1 = rec.build_frames()
    frames2 = rec.build_frames()
    assert frames1 == frames2


def test_recorder_empty_when_no_events_recorded() -> None:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    assert rec.build_frames() == ()
