"""Unit tests for SolverRuntimeReplayRecorder (Phase 9F/9G contracts).

Tests focus on:
- Frame ordering and event_type sequence
- Phase assignments
- map_view renderability
- Frame index monotonicity
- Source immutability (recorder must not mutate loaded snapshot)
"""

from __future__ import annotations

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.optimization.candidate_dtos import (
    CandidateGenerationResult,
    GeneCandidate,
    RejectedGeneCandidate,
)
from django_apps.asteroid_lab.optimization.candidate_selector import SelectedCandidatePlan
from django_apps.asteroid_lab.optimization.capacity_planner import CapacityPlan
from django_apps.asteroid_lab.optimization.commit_best_candidates import (
    ConfirmedGenePlacement,
    IncrementalCommitResult,
    SkippedCandidateRecord,
)
from django_apps.asteroid_lab.optimization.enums import (
    CandidateRejectReason,
    CommitConflictReason,
    Direction,
    PlacementCommitState,
    ReservationState,
    RouteGoalKind,
    RouteProbeFailureReason,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    RouteGoal,
    RouteReservation,
    ValidationResult,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.loaded_snapshot import (
    LoadedReconstructionSnapshot,
    loaded_reconstruction_snapshot_from_run,
)
from django_apps.asteroid_lab.optimization.materialization_dtos import (
    MaterializedLayoutCells,
    RouteMaterializationResult,
)
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_loaded_snapshot,
)
from django_apps.asteroid_lab.optimization.route_goal_planner import PlannedRouteGoals
from django_apps.asteroid_lab.optimization.route_probe import RouteProbeResult
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.replay.projection_context import ReplayProjectionContext
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.replay_recording_cells import (
    visible_cells_from_loaded_snapshot,
)
from django_apps.asteroid_lab.replay.solver_runtime_replay_recorder import (
    SolverRuntimeReplayRecorder,
)
from django_apps.asteroid_lab.replay.timeline_dtos import replay_map_view_is_renderable
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO

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


def _skipped_records(
    *candidate_ids: str,
    reason: CommitConflictReason = CommitConflictReason.ROUTE_PROBE_FAILED,
) -> tuple[SkippedCandidateRecord, ...]:
    return tuple(SkippedCandidateRecord(candidate_id=cid, reason=reason) for cid in candidate_ids)


def _minimal_capacity() -> CapacityPlan:
    return CapacityPlan(
        mineable_cell_count=3,
        estimated_extractor_groups=0,
        shape_goal_count=0,
        fluid_goal_count=0,
        packing_efficiency=0.75,
        platform_footprint_cells=5,
    )


def _empty_planned_route_goals(
    capacity: CapacityPlan | None = None,
) -> PlannedRouteGoals:
    cap = capacity if capacity is not None else _minimal_capacity()
    return PlannedRouteGoals(
        goals=frozenset(),
        capacity_plan=cap,
        shape_goals_requested=0,
        shape_goals_placed=0,
        fluid_goals_requested=0,
        fluid_goals_placed=0,
        selected_cardinal=None,
        spread_axis=None,
    )


def _full_recorder_run() -> SolverRuntimeReplayRecorder:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    inp = greenfield_optimization_input()
    capacity = _minimal_capacity()
    planned = _empty_planned_route_goals(capacity)
    pool = CandidateGenerationResult(normal_candidates=(), rejected_candidates=())
    plan = SelectedCandidatePlan(ordered_candidate_ids=())
    commit = IncrementalCommitResult(
        confirmed=(), skipped_candidates=(), goal_assigned_platforms={}
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
        assert replay_map_view_is_renderable(
            frame.map_view
        ), f"Frame {frame.event_type} is not renderable"


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


def _hole_blueprint_snapshot() -> DecodedBlueprintSnapshotDTO:
    cells = (
        DecodedCellDTO(
            x=1,
            y=0,
            layer=None,
            rotation=0,
            tile_type="",
            cell_kind="fluid_miner",
            transport_kind="none",
            has_nested_blueprint=False,
            nested_entry_count=0,
            nested_type_counts_json={},
            raw_entry_json={},
        ),
        DecodedCellDTO(
            x=2,
            y=0,
            layer=None,
            rotation=0,
            tile_type="",
            cell_kind="space_pipe",
            transport_kind="fluid_pipe",
            has_nested_blueprint=False,
            nested_entry_count=0,
            nested_type_counts_json={},
            raw_entry_json={},
        ),
        DecodedCellDTO(
            x=1,
            y=1,
            layer=None,
            rotation=0,
            tile_type="UnknownTile_A",
            cell_kind="unknown",
            transport_kind="none",
            has_nested_blueprint=False,
            nested_entry_count=0,
            nested_type_counts_json={},
            raw_entry_json={},
        ),
    )
    return DecodedBlueprintSnapshotDTO(
        project_id=None,
        map_input_id=None,
        binary_version=3,
        blueprint_type="Island",
        entry_count=len(cells),
        bbox_json={"min_x": 1, "max_x": 2, "min_y": 0, "max_y": 1, "width": 2, "height": 2},
        cell_kind_counts_json={},
        transport_kind_counts_json={},
        cells=cells,
        summary_json={},
    )


def test_record_optimization_input_loaded_uses_full_loaded_snapshot() -> None:
    snap = _hole_blueprint_snapshot()
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    loaded = loaded_reconstruction_snapshot_from_run(cleanup, recon)
    assert loaded.server_xy_params is not None
    params = loaded.server_xy_params
    rec = SolverRuntimeReplayRecorder(loaded, params)
    inp = optimization_input_from_loaded_snapshot(loaded)
    rec.record_optimization_input_loaded(inp)
    frame = rec.build_frames()[0]
    assert frame.event_type == ReplayEventType.OPTIMIZATION_INPUT_LOADED
    ctx = ReplayProjectionContext(server_xy_params=params)
    expected_cells = visible_cells_from_loaded_snapshot(loaded, ctx)
    assert frame.map_view.full_cells == expected_cells
    assert len(expected_cells) > len(inp.mineable_cells | inp.rim_cells)
    assert frame.inspector["full_cell_count"] == len(expected_cells)
    assert frame.inspector["source_cell_count"] == len(loaded.cells)
    assert frame.inspector["truncated"] is False
    assert frame.inspector["asteroid_bbox"]["min_sx"] == inp.asteroid_bbox.min_sx
    assert frame.inspector["route_domain_bbox"]["max_sx"] == inp.route_domain_bbox.max_sx
    assert frame.inspector["outer_void_padding"] == 10
    assert frame.inspector["external_void_cell_count"] == len(inp.external_void_cells)
    assert frame.inspector["route_domain_cell_count"] > len(inp.mineable_cells)


def test_recorder_build_frames_is_idempotent() -> None:
    rec = _full_recorder_run()
    frames1 = rec.build_frames()
    frames2 = rec.build_frames()
    assert frames1 == frames2


def test_recorder_empty_when_no_events_recorded() -> None:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    assert rec.build_frames() == ()


def _probe_result(
    *,
    reachable: bool = True,
    path: tuple[tuple[int, int], ...] = (),
) -> RouteProbeResult:
    goal = RouteGoal(
        coord=(2, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    return RouteProbeResult(
        reachable=reachable,
        path=path,
        cost=len(path),
        expanded_nodes=3,
        reached_goal=goal if reachable else None,
        goal_priority=goal.priority if reachable else None,
        failure_reason=None if reachable else RouteProbeFailureReason.EXHAUSTED,
    )


def _minimal_gene_candidate(
    candidate_id: str = "g:0,0:e:shape_belt",
    *,
    path: tuple[tuple[int, int], ...] = ((0, 0), (1, 0), (2, 0)),
) -> GeneCandidate:
    extractor = (0, 0)
    probe = _probe_result(path=path)
    return GeneCandidate(
        candidate_id=candidate_id,
        gene_id="test_gene",
        topology_signature="sig",
        extractor=extractor,
        extensions=((1, 0),),
        occupied_cells=frozenset({extractor, (1, 0)}),
        route_probe_start=(0, 0),
        fixed_output_transport=(1, 0),
        output_dir=Direction.E,
        transport_kind=TransportKind.SHAPE_BELT,
        base_throughput=8,
        base_score=8.0,
        route_probe_result=probe,
    )


def test_route_probe_succeeded_frame_includes_path_overlay() -> None:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    candidate = _minimal_gene_candidate()
    pool = CandidateGenerationResult(normal_candidates=(candidate,), rejected_candidates=())
    rec.record_candidate_pool_details(pool)

    probe_frame = next(
        f for f in rec.build_frames() if f.event_type == ReplayEventType.ROUTE_PROBE_SUCCEEDED
    )
    overlay_kinds = {c.kind for c in probe_frame.map_view.overlay_cells}
    assert "route_probe" in overlay_kinds
    assert len(probe_frame.map_view.overlay_cells) == len(candidate.route_probe_result.path)


def test_record_route_goals_generated_includes_goal_overlay() -> None:

    from django_apps.asteroid_lab.optimization.enums import RouteGoalKind
    from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal
    from django_apps.asteroid_lab.optimization.route_goal_planner import PlannedRouteGoals

    loaded = _minimal_loaded()
    capacity = _minimal_capacity()
    goal = RouteGoal(
        coord=(3, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=20,
        existing_trunk=False,
    )
    planned = PlannedRouteGoals(
        goals=frozenset({goal}),
        capacity_plan=capacity,
        shape_goals_requested=1,
        shape_goals_placed=1,
        fluid_goals_requested=0,
        fluid_goals_placed=0,
        selected_cardinal=Direction.E,
        spread_axis="x",
    )
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    rec.record_route_goals_generated(planned)
    frame = rec.build_frames()[0]
    assert frame.event_type == ReplayEventType.ROUTE_GOAL_GENERATED
    overlay_kinds = {c.kind for c in frame.map_view.overlay_cells}
    assert "route_goal" in overlay_kinds
    assert frame.inspector["shape_goals_requested"] == 1


def test_route_goal_overlay_persists_until_result_layout() -> None:
    from dataclasses import replace

    from django_apps.asteroid_lab.optimization.enums import RouteGoalKind
    from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal
    from django_apps.asteroid_lab.optimization.route_goal_planner import PlannedRouteGoals

    loaded = _minimal_loaded()
    capacity = replace(_minimal_capacity(), shape_goal_count=1)
    goal = RouteGoal(
        coord=(3, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=20,
        existing_trunk=False,
    )
    planned = PlannedRouteGoals(
        goals=frozenset({goal}),
        capacity_plan=capacity,
        shape_goals_requested=1,
        shape_goals_placed=1,
        fluid_goals_requested=0,
        fluid_goals_placed=0,
        selected_cardinal=Direction.E,
        spread_axis="x",
    )
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    rec.record_route_goals_generated(planned)
    rec.record_candidate_pool_completed(
        CandidateGenerationResult(normal_candidates=(), rejected_candidates=())
    )
    rec.record_result_layout(
        commit=IncrementalCommitResult(
            confirmed=(), skipped_candidates=(), goal_assigned_platforms={}
        ),
        materialization=RouteMaterializationResult(
            layout=MaterializedLayoutCells(cells=()), failure_reason=None
        ),
        validation=ValidationResult(passed=True, issues=()),
        solver_summary={"issue_codes": []},
    )
    goal_idx = next(
        i
        for i, f in enumerate(rec.build_frames())
        if f.event_type == ReplayEventType.ROUTE_GOAL_GENERATED
    )
    for frame in rec.build_frames()[goal_idx:]:
        kinds = {c.kind for c in frame.map_view.overlay_cells}
        assert "route_goal" in kinds, frame.event_type


def test_record_candidate_pool_details_emits_generated_and_probe_frames() -> None:
    from django_apps.asteroid_lab.optimization.gene_template import (
        CANONICAL_EXTRACTOR_OFFSET,
        CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
        CANONICAL_OUTPUT_DIR,
        CANONICAL_ROUTE_PROBE_START_OFFSET,
        GeneTemplate,
    )

    loaded = _minimal_loaded()
    tpl = GeneTemplate(
        gene_id="test_gene",
        name="test",
        occupied_offsets=frozenset({CANONICAL_EXTRACTOR_OFFSET}),
        extractor_offset=CANONICAL_EXTRACTOR_OFFSET,
        extension_offsets=(),
        output_dir=CANONICAL_OUTPUT_DIR,
        fixed_output_transport_offset=CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
        route_probe_start_offset=CANONICAL_ROUTE_PROBE_START_OFFSET,
        throughput_factor=8,
        topology_signature_base="test_gene",
    )
    rec = SolverRuntimeReplayRecorder(
        loaded, _SERVER_XY_PARAMS, gene_templates_by_id={tpl.gene_id: tpl}
    )
    candidate = _minimal_gene_candidate()
    pool = CandidateGenerationResult(normal_candidates=(candidate,), rejected_candidates=())
    rec.record_candidate_pool_details(pool)

    event_types = [f.event_type for f in rec.build_frames()]
    assert ReplayEventType.CANDIDATE_GENERATED in event_types
    assert ReplayEventType.ROUTE_PROBE_SUCCEEDED in event_types
    gen_frame = next(
        f for f in rec.build_frames() if f.event_type == ReplayEventType.CANDIDATE_GENERATED
    )
    assert gen_frame.inspector["candidate_id"] == candidate.candidate_id
    assert gen_frame.map_view.overlay_cells
    assert gen_frame.map_view.overlay_cells[0].kind == "shape_miner"


def test_record_route_materialized_includes_equipment_cell_delta() -> None:
    from django_apps.asteroid_lab.optimization.gene_template import (
        CANONICAL_EXTRACTOR_OFFSET,
        CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
        CANONICAL_OUTPUT_DIR,
        CANONICAL_ROUTE_PROBE_START_OFFSET,
        GeneTemplate,
    )
    from django_apps.asteroid_lab.optimization.placement_network_materializer import (
        materialize_confirmed_placements,
        merge_materialized_layout,
    )
    from django_apps.asteroid_lab.optimization.route_network_materializer import (
        materialize_route_network,
    )
    from django_apps.asteroid_lab.replay.replay_recording_cells import (
        materialized_cells_to_cell_delta,
    )

    loaded = _minimal_loaded()
    tpl = GeneTemplate(
        gene_id="test_gene",
        name="test",
        occupied_offsets=frozenset({CANONICAL_EXTRACTOR_OFFSET}),
        extractor_offset=CANONICAL_EXTRACTOR_OFFSET,
        extension_offsets=(),
        output_dir=CANONICAL_OUTPUT_DIR,
        fixed_output_transport_offset=CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
        route_probe_start_offset=CANONICAL_ROUTE_PROBE_START_OFFSET,
        throughput_factor=8,
        topology_signature_base="test_gene",
    )
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    base_probe = _minimal_gene_candidate().route_probe_result
    assert base_probe.reached_goal is not None
    probe = RouteProbeResult(
        reachable=True,
        path=((1, 0), (2, 0), (3, 0)),
        cost=3,
        expanded_nodes=3,
        reached_goal=base_probe.reached_goal,
        goal_priority=base_probe.goal_priority,
        failure_reason=None,
    )
    candidate = GeneCandidate(
        candidate_id="g:0,0:e:shape_belt",
        gene_id="test_gene",
        topology_signature="sig",
        extractor=(0, 0),
        extensions=(),
        occupied_cells=frozenset({(0, 0)}),
        route_probe_start=(2, 0),
        fixed_output_transport=(1, 0),
        output_dir=Direction.E,
        transport_kind=TransportKind.SHAPE_BELT,
        base_throughput=8,
        base_score=8.0,
        route_probe_result=probe,
    )
    probe = candidate.route_probe_result
    assert probe.reached_goal is not None
    fot = candidate.fixed_output_transport
    path = probe.path
    if fot in path:
        path = path[path.index(fot) :]
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id=candidate.candidate_id,
                reservation=RouteReservation(
                    reservation_id=f"{candidate.candidate_id}:route:0",
                    candidate_id=candidate.candidate_id,
                    transport_kind=candidate.transport_kind,
                    path=path,
                    reserved_cells=frozenset(path),
                    cost=probe.cost,
                    reached_goal=probe.reached_goal,
                    goal_priority=probe.goal_priority,
                    reservation_state=ReservationState.CONFIRMED,
                    domain_cell_transitions=(),
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidates=(),
        goal_assigned_platforms={},
    )
    route = materialize_route_network(commit, {candidate.candidate_id: candidate})
    equipment = materialize_confirmed_placements(
        commit, {candidate.candidate_id: candidate}, gene_templates_by_id={tpl.gene_id: tpl}
    )
    merged = merge_materialized_layout(route, equipment)
    assert merged.layout is not None
    rec.record_route_materialized(merged)
    delta = materialized_cells_to_cell_delta(merged.layout, rec._ctx)
    kinds = {d.kind for d in delta}
    assert "shape_miner" in kinds
    route_frame = next(
        f for f in rec.build_frames() if f.event_type == ReplayEventType.ROUTE_MATERIALIZED
    )
    assert route_frame.inspector["materialized_equipment_cell_count"] >= 1
    assert route_frame.map_view.cell_delta == delta


def test_route_materialized_and_result_layout_share_cell_delta() -> None:
    from django_apps.asteroid_lab.optimization.gene_template import (
        CANONICAL_EXTRACTOR_OFFSET,
        CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
        CANONICAL_OUTPUT_DIR,
        CANONICAL_ROUTE_PROBE_START_OFFSET,
        GeneTemplate,
    )
    from django_apps.asteroid_lab.optimization.placement_network_materializer import (
        materialize_confirmed_placements,
        merge_materialized_layout,
    )
    from django_apps.asteroid_lab.optimization.route_network_materializer import (
        materialize_route_network,
    )

    loaded = _minimal_loaded()
    tpl = GeneTemplate(
        gene_id="test_gene",
        name="test",
        occupied_offsets=frozenset({CANONICAL_EXTRACTOR_OFFSET}),
        extractor_offset=CANONICAL_EXTRACTOR_OFFSET,
        extension_offsets=(),
        output_dir=CANONICAL_OUTPUT_DIR,
        fixed_output_transport_offset=CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
        route_probe_start_offset=CANONICAL_ROUTE_PROBE_START_OFFSET,
        throughput_factor=8,
        topology_signature_base="test_gene",
    )
    rec = SolverRuntimeReplayRecorder(
        loaded, _SERVER_XY_PARAMS, gene_templates_by_id={tpl.gene_id: tpl}
    )
    base_probe = _minimal_gene_candidate().route_probe_result
    assert base_probe.reached_goal is not None
    probe = RouteProbeResult(
        reachable=True,
        path=((1, 0), (2, 0), (3, 0)),
        cost=3,
        expanded_nodes=3,
        reached_goal=base_probe.reached_goal,
        goal_priority=base_probe.goal_priority,
        failure_reason=None,
    )
    candidate = GeneCandidate(
        candidate_id="g:0,0:e:shape_belt",
        gene_id="test_gene",
        topology_signature="sig",
        extractor=(0, 0),
        extensions=(),
        occupied_cells=frozenset({(0, 0)}),
        route_probe_start=(2, 0),
        fixed_output_transport=(1, 0),
        output_dir=Direction.E,
        transport_kind=TransportKind.SHAPE_BELT,
        base_throughput=8,
        base_score=8.0,
        route_probe_result=probe,
    )
    assert candidate.route_probe_result.reached_goal is not None
    fot = candidate.fixed_output_transport
    path = candidate.route_probe_result.path
    if fot in path:
        path = path[path.index(fot) :]
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id=candidate.candidate_id,
                reservation=RouteReservation(
                    reservation_id=f"{candidate.candidate_id}:route:0",
                    candidate_id=candidate.candidate_id,
                    transport_kind=candidate.transport_kind,
                    path=path,
                    reserved_cells=frozenset(path),
                    cost=probe.cost,
                    reached_goal=probe.reached_goal,
                    goal_priority=probe.goal_priority,
                    reservation_state=ReservationState.CONFIRMED,
                    domain_cell_transitions=(),
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidates=(),
        goal_assigned_platforms={},
    )
    route = materialize_route_network(commit, {candidate.candidate_id: candidate})
    equipment = materialize_confirmed_placements(
        commit, {candidate.candidate_id: candidate}, gene_templates_by_id={tpl.gene_id: tpl}
    )
    merged = merge_materialized_layout(route, equipment)
    assert merged.layout is not None
    validation = ValidationResult(passed=True, issues=())
    rec.record_route_materialized(merged)
    rec.record_result_layout(
        commit=commit,
        materialization=merged,
        validation=validation,
        solver_summary={"issue_codes": []},
    )
    route_frame = next(
        f for f in rec.build_frames() if f.event_type == ReplayEventType.ROUTE_MATERIALIZED
    )
    result_frame = next(
        f for f in rec.build_frames() if f.event_type == ReplayEventType.RESULT_LAYOUT
    )
    assert route_frame.map_view.cell_delta == result_frame.map_view.cell_delta


def test_candidate_generated_keeps_equipment_in_overlay_not_full_cells() -> None:
    loaded = _minimal_loaded()
    from django_apps.asteroid_lab.optimization.gene_template import (
        CANONICAL_EXTRACTOR_OFFSET,
        CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
        CANONICAL_OUTPUT_DIR,
        CANONICAL_ROUTE_PROBE_START_OFFSET,
        GeneTemplate,
    )

    tpl = GeneTemplate(
        gene_id="test_gene",
        name="test",
        occupied_offsets=frozenset({CANONICAL_EXTRACTOR_OFFSET}),
        extractor_offset=CANONICAL_EXTRACTOR_OFFSET,
        extension_offsets=(),
        output_dir=CANONICAL_OUTPUT_DIR,
        fixed_output_transport_offset=CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
        route_probe_start_offset=CANONICAL_ROUTE_PROBE_START_OFFSET,
        throughput_factor=8,
        topology_signature_base="test_gene",
    )
    rec = SolverRuntimeReplayRecorder(
        loaded, _SERVER_XY_PARAMS, gene_templates_by_id={tpl.gene_id: tpl}
    )
    candidate = _minimal_gene_candidate()
    pool = CandidateGenerationResult(normal_candidates=(candidate,), rejected_candidates=())
    rec.record_candidate_pool_details(pool)
    gen_frame = next(
        f for f in rec.build_frames() if f.event_type == ReplayEventType.CANDIDATE_GENERATED
    )
    overlay_kinds = {c.kind for c in gen_frame.map_view.overlay_cells}
    full_kinds = {c.kind for c in gen_frame.map_view.full_cells}
    assert "shape_miner" in overlay_kinds
    assert "shape_miner" not in full_kinds


def test_materialized_cell_delta_emits_transport_before_equipment() -> None:
    from django_apps.asteroid_lab.optimization.gene_template_loader import (
        gene_template_from_generated_sample,
    )
    from django_apps.asteroid_lab.optimization.placement_network_materializer import (
        materialize_confirmed_placements,
        merge_materialized_layout,
    )
    from django_apps.asteroid_lab.optimization.route_network_materializer import (
        materialize_route_network,
    )
    from django_apps.asteroid_lab.replay.replay_recording_cells import (
        materialized_cells_to_cell_delta,
    )
    from django_apps.asteroid_lab.services.sample_gene_exhaustive_generator import (
        generate_exhaustive_sample_genes,
    )

    genes, _ = generate_exhaustive_sample_genes(max_extensions=0, transport_kinds=("belt",))
    tpl = gene_template_from_generated_sample(genes[0])
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    cand = GeneCandidate(
        candidate_id="order:test",
        gene_id=tpl.gene_id,
        topology_signature="sig",
        extractor=(0, 0),
        extensions=(),
        occupied_cells=frozenset({(0, 0)}),
        route_probe_start=(2, 0),
        fixed_output_transport=(1, 0),
        output_dir=Direction.E,
        transport_kind=TransportKind.SHAPE_BELT,
        base_throughput=8,
        base_score=8.0,
        route_probe_result=RouteProbeResult(
            reachable=True,
            path=((1, 0), (2, 0), (3, 0), (6, 0)),
            cost=4,
            expanded_nodes=4,
            reached_goal=goal,
            goal_priority=10,
            failure_reason=None,
        ),
    )

    probe = cand.route_probe_result
    assert probe.reached_goal is not None
    fot = cand.fixed_output_transport
    path = probe.path
    if fot in path:
        path = path[path.index(fot) :]
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id=cand.candidate_id,
                reservation=RouteReservation(
                    reservation_id="order:test:route:0",
                    candidate_id=cand.candidate_id,
                    transport_kind=cand.transport_kind,
                    path=path,
                    reserved_cells=frozenset(path),
                    cost=probe.cost,
                    reached_goal=probe.reached_goal,
                    goal_priority=probe.goal_priority,
                    reservation_state=ReservationState.CONFIRMED,
                    domain_cell_transitions=(),
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidates=(),
        goal_assigned_platforms={},
    )
    route = materialize_route_network(commit, {cand.candidate_id: cand})
    equipment = materialize_confirmed_placements(
        commit, {cand.candidate_id: cand}, gene_templates_by_id={tpl.gene_id: tpl}
    )
    merged = merge_materialized_layout(route, equipment)
    assert merged.layout is not None
    ctx = ReplayProjectionContext(server_xy_params=_SERVER_XY_PARAMS)
    delta = materialized_cells_to_cell_delta(merged.layout, ctx)
    transport_idxs = [i for i, d in enumerate(delta) if d.kind == "transport"]
    equipment_idxs = [
        i for i, d in enumerate(delta) if d.kind in ("shape_miner", "shape_miner_extension")
    ]
    assert transport_idxs and equipment_idxs
    assert max(transport_idxs) < min(equipment_idxs)


def test_record_candidate_pool_details_emits_rejected_with_probe_frames() -> None:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    rejected = RejectedGeneCandidate(
        attempted_gene_id="gene_x",
        extractor=(0, 0),
        rejection_reason=CandidateRejectReason.ROUTE_PROBE_UNREACHABLE,
        route_probe_result=_probe_result(reachable=False, path=((0, 0), (1, 0))),
    )
    pool = CandidateGenerationResult(normal_candidates=(), rejected_candidates=(rejected,))
    rec.record_candidate_pool_details(pool)

    event_types = [f.event_type for f in rec.build_frames()]
    assert ReplayEventType.CANDIDATE_REJECTED in event_types
    assert ReplayEventType.ROUTE_PROBE_FAILED in event_types


def test_record_candidate_pool_details_caps_at_max_per_type() -> None:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    normals = tuple(_minimal_gene_candidate(f"c{i}") for i in range(5))
    pool = CandidateGenerationResult(normal_candidates=normals, rejected_candidates=())
    rec.record_candidate_pool_details(pool, max_per_type=2)

    assert len(rec.build_frames()) <= 4


def test_record_genome_scaffold_emits_three_genome_frames() -> None:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    plan = SelectedCandidatePlan(ordered_candidate_ids=("c1", "c2"))
    pool = CandidateGenerationResult(
        normal_candidates=(_minimal_gene_candidate("c1"),),
        rejected_candidates=(),
    )
    rec.record_genome_scaffold(plan, pool=pool)

    event_types = [f.event_type for f in rec.build_frames()]
    assert event_types == [
        ReplayEventType.GENOME_EVALUATED,
        ReplayEventType.BEST_GENOME_SELECTED,
        ReplayEventType.GENERATION_COMPLETED,
    ]
    assert rec.build_frames()[0].inspector["evaluated_count"] == 1
    assert rec.build_frames()[1].inspector["best_candidate_ids"] == ["c1", "c2"]


def test_record_commit_details_emits_attempted_and_committed() -> None:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    candidate = _minimal_gene_candidate("commit_ok")
    reservation = RouteReservation(
        reservation_id="commit_ok:route:0",
        candidate_id="commit_ok",
        transport_kind=TransportKind.SHAPE_BELT,
        path=((0, 0), (1, 0)),
        reserved_cells=frozenset({(0, 0), (1, 0)}),
        cost=2,
        reached_goal=candidate.route_probe_result.reached_goal,
        goal_priority=10,
        reservation_state=ReservationState.CONFIRMED,
        domain_cell_transitions=(),
    )
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id="commit_ok",
                reservation=reservation,
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidates=(),
        goal_assigned_platforms={},
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=("commit_ok",))
    rec.record_commit_details(plan, {"commit_ok": candidate}, commit)

    event_types = [f.event_type for f in rec.build_frames()]
    assert event_types == [
        ReplayEventType.ROUTE_COMMIT_ATTEMPTED,
        ReplayEventType.ROUTE_COMMITTED,
    ]
    committed = rec.build_frames()[1]
    assert committed.inspector["reservation_id"] == "commit_ok:route:0"
    assert committed.inspector["reservation_state"] == ReservationState.CONFIRMED.value
    overlay_kinds = {c.kind for c in committed.map_view.overlay_cells}
    assert "confirmed_route" in overlay_kinds
    assert len(committed.map_view.overlay_cells) == len(reservation.path)


def test_record_route_committed_includes_all_confirmed_paths() -> None:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    candidate = _minimal_gene_candidate("commit_ok")
    reservation = RouteReservation(
        reservation_id="commit_ok:route:0",
        candidate_id="commit_ok",
        transport_kind=TransportKind.SHAPE_BELT,
        path=((0, 0), (1, 0)),
        reserved_cells=frozenset({(0, 0), (1, 0)}),
        cost=2,
        reached_goal=candidate.route_probe_result.reached_goal,
        goal_priority=10,
        reservation_state=ReservationState.CONFIRMED,
        domain_cell_transitions=(),
    )
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id="commit_ok",
                reservation=reservation,
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidates=(),
        goal_assigned_platforms={},
    )
    rec.record_route_committed(commit)

    frame = rec.build_frames()[0]
    assert frame.event_type == ReplayEventType.ROUTE_COMMITTED
    assert {c.kind for c in frame.map_view.overlay_cells} == {"confirmed_route"}


def test_record_commit_details_emits_rolled_back_for_skipped() -> None:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    candidate = _minimal_gene_candidate("skip_me")
    commit = IncrementalCommitResult(
        confirmed=(),
        skipped_candidates=_skipped_records("skip_me"),
        goal_assigned_platforms={},
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=("skip_me",))
    rec.record_commit_details(plan, {"skip_me": candidate}, commit)

    event_types = [f.event_type for f in rec.build_frames()]
    assert event_types == [
        ReplayEventType.ROUTE_COMMIT_ATTEMPTED,
        ReplayEventType.ROUTE_ROLLED_BACK,
    ]
    rolled_back = rec.build_frames()[-1]
    assert rolled_back.metrics["commit_conflict_reason"] == "route_probe_failed"
    assert rolled_back.metrics["candidate_id"] == "skip_me"


def test_record_commit_details_caps_at_max_candidates() -> None:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    ids = tuple(f"c{i}" for i in range(5))
    candidates = {cid: _minimal_gene_candidate(cid) for cid in ids}
    commit = IncrementalCommitResult(
        confirmed=(),
        skipped_candidates=_skipped_records(*ids),
        goal_assigned_platforms={},
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=ids)
    rec.record_commit_details(plan, candidates, commit, max_candidates=2)

    assert len(rec.build_frames()) <= 4


def test_full_recorder_with_all_new_methods_frame_index_monotonic() -> None:
    loaded = _minimal_loaded()
    rec = SolverRuntimeReplayRecorder(loaded, _SERVER_XY_PARAMS)
    inp = greenfield_optimization_input()
    capacity = _minimal_capacity()
    planned = _empty_planned_route_goals(capacity)
    candidate = _minimal_gene_candidate("detail_c")
    pool = CandidateGenerationResult(normal_candidates=(candidate,), rejected_candidates=())
    plan = SelectedCandidatePlan(ordered_candidate_ids=("detail_c",))
    commit = IncrementalCommitResult(
        confirmed=(),
        skipped_candidates=_skipped_records("detail_c"),
        goal_assigned_platforms={},
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
    rec.record_candidate_pool_details(pool, max_per_type=1)
    rec.record_candidate_selection_completed(plan)
    rec.record_genome_scaffold(plan, pool=pool)
    rec.record_route_committed(commit)
    rec.record_commit_details(plan, {"detail_c": candidate}, commit, max_candidates=1)
    rec.record_route_materialized(materialization)
    rec.record_validation_completed(validation)
    rec.record_result_layout(
        commit=commit,
        materialization=materialization,
        validation=validation,
        solver_summary=summary,
    )

    frames = rec.build_frames()
    indices = [f.frame_index for f in frames]
    assert indices == list(range(len(indices)))
    assert len(frames) > 9
    detail_types = {
        ReplayEventType.CANDIDATE_GENERATED,
        ReplayEventType.ROUTE_PROBE_SUCCEEDED,
        ReplayEventType.GENOME_EVALUATED,
        ReplayEventType.ROUTE_COMMIT_ATTEMPTED,
        ReplayEventType.ROUTE_ROLLED_BACK,
    }
    assert detail_types.issubset({f.event_type for f in frames})
