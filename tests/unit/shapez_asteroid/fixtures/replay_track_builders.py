"""Deterministic optimization replay-track payloads for narrow-corridor golden JSON (tests only).

Each :func:`expected_*_replay_fixture_v0` runs the same incremental-commit paths as the
referenced regression tests, then freezes
:class:`~django_apps.shapez_asteroid.optimization.dto.OptimizationReplayFrame` tuples via
:func:`~django_apps.shapez_asteroid.optimization.optimization_ui_payload.build_optimization_replay_track_payload`.
Output is **never** solver input; see ``tests/fixtures/shapez_asteroid/replay/*.json``.
"""

from __future__ import annotations

from django_apps.shapez_asteroid.optimization.incremental_commit import commit_best_genome
from django_apps.shapez_asteroid.optimization.optimization_replay import OptimizationReplayRecorder
from django_apps.shapez_asteroid.optimization.optimization_ui_payload import (
    build_optimization_replay_track_payload,
)
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)
from tests.unit.shapez_asteroid.fixtures.narrow_corridor import (
    build_narrow_bridge_optimization_input,
    build_rim_competition_genome,
    build_rim_competition_pool,
    build_symmetric_narrow_bridge_optimization_input,
    build_symmetric_rim_competition_pool,
)


def _envelope(
    *,
    replay_fixture_id: str,
    scenario: str,
    frames_payload: dict[str, object],
) -> dict[str, object]:
    frames = frames_payload["frames"]
    metrics = frames_payload["metrics"]
    assert isinstance(frames, list)
    assert isinstance(metrics, dict)
    seq = [str(item["event_type"]) for item in frames]
    return {
        "schema_version": 1,
        "replay_fixture_id": replay_fixture_id,
        "replay_frames": frames,
        "replay_summary": dict(metrics),
        "replay_event_sequence": seq,
        "metadata": {"scenario": scenario, "contract": "replay_fixture_v0"},
    }


def expected_narrow_corridor_asymmetric_replay_fixture_v0() -> dict[str, object]:
    """Default rim competition commit (left slot 0, right slot 1); mirrors narrow-bridge replay."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    rec = OptimizationReplayRecorder()
    commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=rec)
    track = build_optimization_replay_track_payload(rec.frames)
    return _envelope(
        replay_fixture_id="narrow_corridor_asymmetric_replay_v0",
        scenario="narrow_corridor_asymmetric",
        frames_payload=track,
    )


def expected_narrow_corridor_symmetric_replay_fixture_v0() -> dict[str, object]:
    """Dual rim goals; default ``sym_rim_left`` then ``sym_rim_right`` commit order."""

    inp, _ = build_symmetric_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_symmetric_rim_competition_pool(inp)
    rec = OptimizationReplayRecorder()
    commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=rec)
    track = build_optimization_replay_track_payload(rec.frames)
    return _envelope(
        replay_fixture_id="narrow_corridor_symmetric_replay_v0",
        scenario="narrow_corridor_symmetric",
        frames_payload=track,
    )


def expected_narrow_corridor_starvation_replay_fixture_v0() -> dict[str, object]:
    """Asymmetric strip with **right rim first** in commit order (distinct event/candidate mix).

    Exercises the same starvation class as ``test_commit_order_right_goal_rim_first_*`` but
    freezes replay for golden contract tests.
    """

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, _ = build_rim_competition_pool(inp)
    genome = build_rim_competition_genome(left_commit_order=1, right_commit_order=0)
    rec = OptimizationReplayRecorder()
    commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=rec)
    track = build_optimization_replay_track_payload(rec.frames)
    return _envelope(
        replay_fixture_id="narrow_corridor_starvation_replay_v0",
        scenario="narrow_corridor_starvation_commit_order",
        frames_payload=track,
    )
