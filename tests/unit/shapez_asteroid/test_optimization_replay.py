"""Sequence 8 — full optimization replay timeline (output-only)."""

from __future__ import annotations

import json

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import (
    FitnessBreakdown,
    FitnessMetrics,
    Gene,
    Genome,
    OptimizationInput,
    OptimizationReplayFrame,
    RouteGoal,
    ValidationIssue,
    ValidationResult,
)
from django_apps.shapez_asteroid.optimization.enums import (
    OptimizationReplayEventType,
    RouteGoalKind,
    TransportKind,
    ValidationIssueCode,
    ValidationSeverity,
)
from django_apps.shapez_asteroid.optimization.evolutionary_search import run_evolutionary_search
from django_apps.shapez_asteroid.optimization.final_validation import (
    validate_incremental_commit_result,
)
from django_apps.shapez_asteroid.optimization.incremental_commit import commit_best_genome
from django_apps.shapez_asteroid.optimization.optimization_replay import (
    MAX_REPLAY_CELLS_PER_FRAME,
    NoOpOptimizationReplayRecorder,
    OptimizationReplayRecorder,
    json_safe_replay_value,
    optimization_replay_frame_to_json_dict,
    optimization_replay_frames_to_json_list,
)
from django_apps.shapez_asteroid.optimization.optimization_replay_events import (
    emit_optimization_input_loaded,
    emit_validation_completed,
    optimization_input_loaded_metrics,
)
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)

from .test_evolutionary_search import _bundle as evo_bundle
from .test_evolutionary_search import _goal, _probe_ok, _small_config
from .test_incremental_commit import _bundle as commit_bundle
from .test_incremental_commit import _strip_input


def _fb_sample() -> FitnessBreakdown:
    m = FitnessMetrics(
        selected_candidate_count=2,
        extractor_count=1,
        extension_count=0,
        overlap_count=0,
        unreachable_count=0,
        total_route_cost=3,
        max_trunk_sharing=0,
        narrow_passage_occupied_count=0,
    )
    return FitnessBreakdown(
        extractor_score=1.0,
        extension_score=0.0,
        throughput_score=2.0,
        route_cost_penalty=0.1,
        overlap_penalty=0.0,
        unreachable_penalty=0.0,
        congestion_penalty=0.0,
        orphan_penalty=0.0,
        corridor_block_penalty=0.0,
        future_expansion_penalty=0.0,
        narrow_passage_penalty=0.0,
        trunk_sharing_penalty=0.0,
        dead_end_penalty=0.0,
        route_goal_quality_score=0.0,
        route_goal_priority_penalty=0.0,
        route_fragility_penalty=0.0,
        shared_corridor_pressure_penalty=0.0,
        total=2.9,
        metrics=m,
    )


def test_replay_frame_serializable() -> None:
    fb = _fb_sample()
    frame = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.GENOME_EVALUATED,
        title="t",
        description="d",
        visible_cells=(),
        overlay_cells=(),
        metrics={"fitness_breakdown": fb, "transport_kind": TransportKind.SHAPE_BELT},
    )
    json.dumps(optimization_replay_frame_to_json_dict(frame))


def test_replay_frame_indices_monotonic() -> None:
    r = OptimizationReplayRecorder()
    for i in range(4):
        r.record_replay_frame(
            event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
            title=str(i),
            description="",
            metrics={"i": i},
        )
    assert [f.frame_index for f in r.frames] == [0, 1, 2, 3]


def test_replay_event_type_is_enum() -> None:
    r = OptimizationReplayRecorder()
    r.record_replay_frame(
        event_type=OptimizationReplayEventType.BEST_GENOME_SELECTED,
        title="x",
        description="",
        metrics={},
    )
    assert isinstance(r.frames[0].event_type, OptimizationReplayEventType)


def test_replay_large_payload_truncation() -> None:
    r = OptimizationReplayRecorder()
    big = tuple(range(MAX_REPLAY_CELLS_PER_FRAME + 5))
    r.record_replay_frame(
        event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
        title="big",
        description="",
        visible_cells=big,
        overlay_cells=(),
        metrics={},
    )
    f = r.frames[0]
    assert len(f.visible_cells) + len(f.overlay_cells) <= MAX_REPLAY_CELLS_PER_FRAME
    assert f.metrics.get("replay_truncated") is True
    assert f.metrics.get("truncation_reason") == "max_replay_cells_per_frame"


def test_replay_truncation_marks_metrics() -> None:
    r = OptimizationReplayRecorder(max_frames=2)
    for _ in range(4):
        r.record_replay_frame(
            event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
            title="x",
            description="",
            metrics={},
        )
    assert len(r.frames) == 2
    assert r.frames[-1].metrics.get("replay_truncated") is True
    assert r.frames[-1].metrics.get("truncation_reason") == "max_replay_frames"


def test_noop_replay_recorder_has_no_side_effects() -> None:
    noop = NoOpOptimizationReplayRecorder()
    emit_optimization_input_loaded(
        noop,
        candidate_count=3,
        extra_metrics=optimization_input_loaded_metrics(_strip_input()[0]),
    )
    assert noop.frames == ()


def test_replay_json_safe_serializes_fitness_breakdown() -> None:
    fb = _fb_sample()
    raw = json_safe_replay_value(fb)
    json.dumps(raw)
    assert raw["total"] == 2.9
    assert "metrics" in raw


def test_replay_json_safe_serializes_validation_result() -> None:
    issue = ValidationIssue(
        issue_code=ValidationIssueCode.ORPHAN_TRANSPORT,
        severity=ValidationSeverity.WARNING,
        coord=None,
        candidate_id=None,
        route_reservation_id=None,
        path_index=None,
        route_goal_kind=None,
        transport_kind=TransportKind.SHAPE_BELT,
        message="m",
    )
    vr = ValidationResult(passed=True, issues=(issue,))
    raw = json_safe_replay_value(vr)
    json.dumps(raw)
    assert raw["passed"] is True


def test_replay_json_safe_nested_coord_matches_top_level_coord() -> None:
    c = Coord(3, 4)
    issue = ValidationIssue(
        issue_code=ValidationIssueCode.INVALID_COORD_CONTRACT,
        severity=ValidationSeverity.ERROR,
        coord=c,
        candidate_id="x",
        route_reservation_id=None,
        path_index=None,
        route_goal_kind=None,
        transport_kind=None,
        message="m",
    )
    vr = ValidationResult(passed=False, issues=(issue,))
    nested = json_safe_replay_value(vr)["issues"][0]["coord"]
    assert nested == json_safe_replay_value(c) == {"x": 3, "y": 4}


def test_replay_same_seed_on_off_identical_best_genome() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (
        evo_bundle("a", _probe_ok(goal=g0), throughput=10),
        evo_bundle("b", _probe_ok(goal=g0), throughput=20, extractor=Coord(2, 0)),
    )
    cfg = _small_config()
    off = run_evolutionary_search(cfg, pool, replay_recorder=None)
    rec = OptimizationReplayRecorder()
    on = run_evolutionary_search(cfg, pool, replay_recorder=rec)
    assert off == on
    assert rec.frames


def test_replay_records_evolution_generation_completed() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (
        evo_bundle("a", _probe_ok(goal=g0)),
        evo_bundle("b", _probe_ok(goal=g0), extractor=Coord(3, 0)),
    )
    rec = OptimizationReplayRecorder()
    run_evolutionary_search(_small_config(max_generation=3), pool, replay_recorder=rec)
    gens = [
        f for f in rec.frames if f.event_type is OptimizationReplayEventType.GENERATION_COMPLETED
    ]
    assert len(gens) == 3


def test_replay_records_best_genome_selected() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (evo_bundle("a", _probe_ok(goal=g0)),)
    rec = OptimizationReplayRecorder()
    run_evolutionary_search(_small_config(max_generation=1), pool, replay_recorder=rec)
    assert any(f.event_type is OptimizationReplayEventType.BEST_GENOME_SELECTED for f in rec.frames)


def test_replay_events_do_not_affect_algorithm_result() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (
        evo_bundle("a", _probe_ok(goal=g0)),
        evo_bundle("b", _probe_ok(goal=g0), extractor=Coord(2, 0)),
    )
    cfg = _small_config()
    assert run_evolutionary_search(cfg, pool) == run_evolutionary_search(
        cfg, pool, replay_recorder=OptimizationReplayRecorder()
    )


def test_replay_records_route_commit_events() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        commit_bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)
    rec = OptimizationReplayRecorder()
    commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=rec)
    types = [f.event_type for f in rec.frames]
    assert OptimizationReplayEventType.ROUTE_COMMIT_ATTEMPTED in types
    assert OptimizationReplayEventType.ROUTE_COMMITTED in types


def test_replay_records_route_rolled_back() -> None:
    inp, _goal = _strip_input()
    inp2 = OptimizationInput(
        asteroid_cells=inp.asteroid_cells,
        mineable_cells=inp.mineable_cells,
        rim_cells=inp.rim_cells,
        interior_cells=inp.interior_cells,
        external_void_cells=inp.external_void_cells,
        route_goals=frozenset(),
        existing_transport_cells=inp.existing_transport_cells,
        existing_trunk_cells=inp.existing_trunk_cells,
        protected_corridor_cells=inp.protected_corridor_cells,
        blocked_cells=inp.blocked_cells,
        topology_graph=inp.topology_graph,
        bbox=inp.bbox,
    )
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    g0 = RouteGoal(c2, RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    pool = (
        commit_bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=g0,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)
    rec = OptimizationReplayRecorder()
    commit_best_genome(genome, pool, inp2, RouteDomainSnapshotBuilder, replay_recorder=rec)
    assert any(f.event_type is OptimizationReplayEventType.ROUTE_ROLLED_BACK for f in rec.frames)


def test_replay_records_validation_completed() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        commit_bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)
    commit_res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    rec = OptimizationReplayRecorder()
    validate_incremental_commit_result(inp, pool, commit_res, replay_recorder=rec)
    assert any(f.event_type is OptimizationReplayEventType.VALIDATION_COMPLETED for f in rec.frames)


def test_replay_commit_replay_does_not_change_commit_result() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        commit_bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)
    off = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    on = commit_best_genome(
        genome, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=OptimizationReplayRecorder()
    )
    assert off == on


def test_replay_validation_replay_does_not_change_validation_result() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        commit_bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)
    commit_res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    off = validate_incremental_commit_result(inp, pool, commit_res)
    on = validate_incremental_commit_result(
        inp, pool, commit_res, replay_recorder=OptimizationReplayRecorder()
    )
    assert off == on


def test_replay_does_not_require_ui_or_database() -> None:
    """Replay helpers stay free of ORM imports in this package slice."""
    import django_apps.shapez_asteroid.optimization.optimization_replay as orp
    import django_apps.shapez_asteroid.optimization.optimization_replay_events as ore

    src = (getattr(orp, "__file__", "") or "") + (getattr(ore, "__file__", "") or "")
    assert "django.db" not in src
    r = OptimizationReplayRecorder()
    emit_validation_completed(
        r,
        result=ValidationResult(passed=True, issues=()),
        route_reservation_ids=(),
    )
    optimization_replay_frames_to_json_list(r.frames)


def test_replay_optimization_input_loaded_helper() -> None:
    inp, _ = _strip_input()
    r = OptimizationReplayRecorder()
    emit_optimization_input_loaded(
        r,
        candidate_count=5,
        extra_metrics=optimization_input_loaded_metrics(inp),
    )
    assert r.frames[0].event_type is OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED
    assert r.frames[0].metrics.get("candidate_count") == 5
