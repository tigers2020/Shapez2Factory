"""Sequence 3B — optimization replay skeleton (output-only)."""

from __future__ import annotations

import json
from dataclasses import replace

from django_apps.shapez_asteroid.optimization.bundle_candidate_generator import (
    generate_bundle_candidates,
)
from django_apps.shapez_asteroid.optimization.dto import (
    CandidateGenerationConfig,
    OptimizationReplayFrame,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CandidateRejectReason,
    ExtractorPlacementPolicy,
    OptimizationReplayEventType,
    RouteProbeFailureReason,
    TransportKind,
)
from django_apps.shapez_asteroid.optimization.optimization_replay import (
    MAX_REPLAY_CELLS_PER_FRAME,
    NoOpOptimizationReplayRecorder,
    OptimizationReplayRecorder,
    optimization_replay_frame_to_json_dict,
)
from django_apps.shapez_asteroid.optimization.pattern_library import build_pattern_library
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)

from .test_candidate_route_probe_integration import _greenfield_square_input


def test_replay_frame_serializable() -> None:
    frame = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
        title="t",
        description="d",
        visible_cells=(),
        overlay_cells=(),
        metrics={"transport_kind": TransportKind.SHAPE_BELT, "n": 1},
    )
    payload = optimization_replay_frame_to_json_dict(frame)
    json.dumps(payload)


def test_replay_frame_indices_monotonic() -> None:
    r = OptimizationReplayRecorder()
    for i in range(5):
        r.record_replay_frame(
            event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
            title=str(i),
            description="",
            metrics={"i": i},
        )
    idx = [f.frame_index for f in r.frames]
    assert idx == [0, 1, 2, 3, 4]
    assert idx == sorted(idx)


def test_replay_event_type_is_enum() -> None:
    r = OptimizationReplayRecorder()
    r.record_replay_frame(
        event_type=OptimizationReplayEventType.ROUTE_PROBE_SUCCEEDED,
        title="ok",
        description="",
        metrics={},
    )
    assert isinstance(r.frames[0].event_type, OptimizationReplayEventType)


def test_replay_large_payload_truncation() -> None:
    r = OptimizationReplayRecorder()
    big = tuple({"i": i} for i in range(MAX_REPLAY_CELLS_PER_FRAME + 40))
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
    assert r.replay_truncated is True


def test_replay_max_frames_cap_sets_truncated_metric() -> None:
    r = OptimizationReplayRecorder(max_frames=3)
    for _ in range(5):
        r.record_replay_frame(
            event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
            title="x",
            description="",
            metrics={},
        )
    assert len(r.frames) == 3
    assert r.frames[-1].metrics.get("replay_truncated") is True
    assert r.replay_truncated is True


def test_replay_disabled_noop_has_no_side_effect() -> None:
    noop = NoOpOptimizationReplayRecorder()
    noop.record_replay_frame(
        event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
        title="n",
        description="",
        metrics={"a": 1},
    )
    assert noop.frames == ()
    assert noop.replay_truncated is False


def test_replay_frame_manual_enum_metrics_roundtrip_json() -> None:
    frame = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.ROUTE_PROBE_FAILED,
        title="fail",
        description="",
        visible_cells=(),
        overlay_cells=(),
        metrics={
            "candidate_reject_reason": CandidateRejectReason.ROUTE_PROBE_UNREACHABLE,
            "route_probe_failure_reason": RouteProbeFailureReason.BUDGET_EXCEEDED,
        },
    )
    d = optimization_replay_frame_to_json_dict(frame)
    assert (
        d["metrics"]["candidate_reject_reason"]
        == CandidateRejectReason.ROUTE_PROBE_UNREACHABLE.value
    )
    assert (
        d["metrics"]["route_probe_failure_reason"] == RouteProbeFailureReason.BUDGET_EXCEEDED.value
    )


def test_replay_truncation_patches_last_frame_metrics() -> None:
    r = OptimizationReplayRecorder(max_frames=2)
    r.record_replay_frame(
        event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
        title="a",
        description="",
        metrics={"replay_truncated": False},
    )
    r.record_replay_frame(
        event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
        title="b",
        description="",
        metrics={"replay_truncated": False},
    )
    r.record_replay_frame(
        event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
        title="c",
        description="",
        metrics={},
    )
    assert len(r.frames) == 2
    assert r.frames[-1].metrics.get("replay_truncated") is True


def test_replay_candidate_generated_event_recorded() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=500,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    rec = OptimizationReplayRecorder()
    generate_bundle_candidates(inp, domain, build_pattern_library(), cfg, replay_recorder=rec)
    types = [f.event_type for f in rec.frames]
    assert OptimizationReplayEventType.CANDIDATE_GENERATED in types


def test_replay_candidate_rejected_event_recorded() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=500,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    rec = OptimizationReplayRecorder()
    generate_bundle_candidates(inp, domain, build_pattern_library(), cfg, replay_recorder=rec)
    types = [f.event_type for f in rec.frames]
    assert OptimizationReplayEventType.CANDIDATE_REJECTED in types


def test_replay_route_probe_success_and_failure_events_recorded() -> None:
    inp = replace(_greenfield_square_input(), route_goals=frozenset())
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=0,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    rec = OptimizationReplayRecorder()
    generate_bundle_candidates(inp, domain, build_pattern_library(), cfg, replay_recorder=rec)
    types = [f.event_type for f in rec.frames]
    assert OptimizationReplayEventType.ROUTE_PROBE_FAILED in types
    inp2 = _greenfield_square_input()
    rec2 = OptimizationReplayRecorder()
    generate_bundle_candidates(
        inp2,
        RouteDomainSnapshotBuilder.build_seed_snapshot(inp2),
        build_pattern_library(),
        CandidateGenerationConfig(
            extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
            allow_diagnostic_unreachable=True,
            max_candidates=None,
            route_probe_max_expansions=500,
            transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
            route_probe_goal_priority_weight=10,
        ),
        replay_recorder=rec2,
    )
    assert OptimizationReplayEventType.ROUTE_PROBE_SUCCEEDED in [f.event_type for f in rec2.frames]


def test_replay_same_seed_or_same_input_on_off_identical_candidate_pools() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=20,
        route_probe_max_expansions=500,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    patterns = build_pattern_library()
    off = generate_bundle_candidates(inp, domain, patterns, cfg, replay_recorder=None)
    rec = OptimizationReplayRecorder()
    on = generate_bundle_candidates(inp, domain, patterns, cfg, replay_recorder=rec)
    assert tuple(c.candidate_id for c in off.normal_candidates) == tuple(
        c.candidate_id for c in on.normal_candidates
    )
    assert len(off.rejected_candidates) == len(on.rejected_candidates)
    assert rec.frames


def test_optimization_replay_frame_replace_keeps_enum() -> None:
    f = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
        title="",
        description="",
        visible_cells=(),
        overlay_cells=(),
        metrics={},
    )
    f2 = replace(f, metrics={"replay_truncated": True})
    assert isinstance(f2.event_type, OptimizationReplayEventType)
