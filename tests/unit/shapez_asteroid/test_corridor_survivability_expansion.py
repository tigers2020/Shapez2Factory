"""Sequence 10B expansion — narrow corridor survivability (GitHub #14).

Reservation pressure vs pool-time probe, replay fragments, commit order, evolution→commit replay.
"""

from __future__ import annotations

from django_apps.shapez_asteroid.optimization.dto import EvolutionConfig, Gene, Genome
from django_apps.shapez_asteroid.optimization.enums import (
    CommitConflictReason,
    OptimizationReplayEventType,
    PenaltyMode,
    PlacementCommitState,
)
from django_apps.shapez_asteroid.optimization.evolutionary_search import run_evolutionary_search
from django_apps.shapez_asteroid.optimization.incremental_commit import commit_best_genome
from django_apps.shapez_asteroid.optimization.optimization_replay import OptimizationReplayRecorder
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)

from .fixtures.narrow_corridor import (
    build_narrow_bridge_optimization_input,
    build_rim_competition_genome,
    build_rim_competition_pool,
    narrow_bridge_coords,
)


def _narrow_evo_config() -> EvolutionConfig:
    return EvolutionConfig(
        seed=9001,
        population_size=8,
        elite_count=2,
        mutation_rate=0.35,
        tournament_size=3,
        max_generation=14,
        max_stall_generation=5,
        time_budget_ms=None,
        forced_distant_mutation_period=None,
    )


def test_reservation_accumulation_records_bridge_cells_before_starvation() -> None:
    """First commit reserves the shared bridge path; second rollback is probe starvation."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, _ = build_rim_competition_pool(inp)
    genome = build_rim_competition_genome(left_commit_order=0, right_commit_order=1)
    c1, c2 = narrow_bridge_coords()[1], narrow_bridge_coords()[2]

    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    assert len(res.route_reservations) == 1
    r0 = res.route_reservations[0]
    assert r0.candidate_id == "rim_left"
    assert c1 in r0.reserved_cells
    assert c2 in r0.reserved_cells
    assert res.candidate_results[1].commit_state is PlacementCommitState.ROLLED_BACK
    assert res.candidate_results[1].conflict_reason is CommitConflictReason.ROUTE_PROBE_FAILED


def test_corridor_starvation_replay_event_subsequence() -> None:
    """Replay shows attempt→commit→attempt→rollback→survivability (narrow starvation)."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    rec = OptimizationReplayRecorder()
    commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=rec)

    types = [f.event_type for f in rec.frames]
    assert OptimizationReplayEventType.ROUTE_COMMIT_ATTEMPTED in types
    assert OptimizationReplayEventType.ROUTE_COMMITTED in types
    assert OptimizationReplayEventType.ROUTE_ROLLED_BACK in types
    assert OptimizationReplayEventType.COMMIT_SURVIVABILITY_SUMMARY in types

    first_attempt = types.index(OptimizationReplayEventType.ROUTE_COMMIT_ATTEMPTED)
    first_commit = types.index(OptimizationReplayEventType.ROUTE_COMMITTED)
    second_attempt = types.index(
        OptimizationReplayEventType.ROUTE_COMMIT_ATTEMPTED,
        first_attempt + 1,
    )
    rollback = types.index(OptimizationReplayEventType.ROUTE_ROLLED_BACK)
    summary = types.index(OptimizationReplayEventType.COMMIT_SURVIVABILITY_SUMMARY)

    assert first_attempt < first_commit < second_attempt < rollback < summary


def test_commit_order_right_goal_rim_first_rolls_back_then_peer_uses_bridge() -> None:
    """Goal sits on ``rim_right``; that rim cannot win slot 0 (output stub vs own occupied overlay).

    After it rolls back, ``rim_left`` still confirms through the bridge — ordering still matters.
    """

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, _ = build_rim_competition_pool(inp)

    g_left_first = build_rim_competition_genome(left_commit_order=0, right_commit_order=1)
    r1 = commit_best_genome(g_left_first, pool, inp, RouteDomainSnapshotBuilder)
    assert r1.candidate_results[0].commit_state is PlacementCommitState.CONFIRMED
    assert r1.candidate_results[0].candidate_id == "rim_left"
    assert r1.candidate_results[1].commit_state is PlacementCommitState.ROLLED_BACK

    g_right_first = build_rim_competition_genome(left_commit_order=1, right_commit_order=0)
    r2 = commit_best_genome(g_right_first, pool, inp, RouteDomainSnapshotBuilder)
    assert r2.candidate_results[0].candidate_id == "rim_right"
    assert r2.candidate_results[0].commit_state is PlacementCommitState.ROLLED_BACK
    assert r2.candidate_results[1].candidate_id == "rim_left"
    assert r2.candidate_results[1].commit_state is PlacementCommitState.CONFIRMED


def test_late_commit_slot_unreachable_after_peer_reservation() -> None:
    """A later commit_order gene for the losing rim still rolls back after the bridge is taken."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, _ = build_rim_competition_pool(inp)
    genome = Genome(
        "narrow_triple",
        (
            Gene("rim_left", True, 0),
            Gene("rim_right", True, 1),
            Gene("rim_right", True, 2),
        ),
        seed=3,
    )

    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    assert len(res.candidate_results) == 3
    assert res.candidate_results[0].commit_state is PlacementCommitState.CONFIRMED
    assert res.candidate_results[1].commit_state is PlacementCommitState.ROLLED_BACK
    assert res.candidate_results[2].commit_state is PlacementCommitState.ROLLED_BACK
    assert res.candidate_results[2].conflict_reason is CommitConflictReason.ROUTE_PROBE_FAILED
    assert res.confirmed_candidate_count == 1
    assert res.rolled_back_candidate_count == 2


def test_evolution_then_commit_replay_stitching_order() -> None:
    """One recorder: evolution ends with BEST_GENOME_SELECTED, then commit survivability tail."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, _ = build_rim_competition_pool(inp)
    rec = OptimizationReplayRecorder()
    evo = run_evolutionary_search(
        _narrow_evo_config(),
        pool,
        route_domain=None,
        replay_recorder=rec,
        penalty_mode=PenaltyMode.CONSERVATIVE,
    )
    commit_best_genome(
        evo.best_genome,
        pool,
        inp,
        RouteDomainSnapshotBuilder,
        replay_recorder=rec,
    )

    types = [f.event_type for f in rec.frames]
    assert OptimizationReplayEventType.BEST_GENOME_SELECTED in types
    assert OptimizationReplayEventType.GENOME_EVALUATED in types
    idx_best = types.index(OptimizationReplayEventType.BEST_GENOME_SELECTED)
    idx_first_commit_attempt = types.index(OptimizationReplayEventType.ROUTE_COMMIT_ATTEMPTED)
    assert idx_best < idx_first_commit_attempt
    assert types[-1] is OptimizationReplayEventType.COMMIT_SURVIVABILITY_SUMMARY
