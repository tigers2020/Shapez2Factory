"""Sequence 10A/10B — narrow corridor regression (probe vs commit, penalties, replay invariant)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.optimization.dto import (
    BundleCandidate,
    EvolutionConfig,
    Gene,
    Genome,
    RouteProbeInput,
    RouteProbeResult,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CardinalDirection,
    CommitConflictReason,
    OptimizationReplayEventType,
    PenaltyMode,
    PlacementCommitState,
    RouteClass,
    TransportKind,
)
from django_apps.shapez_asteroid.optimization.evolutionary_search import run_evolutionary_search
from django_apps.shapez_asteroid.optimization.genome_fitness import (
    evaluate_genome,
    fitness_breakdown_total_matches_components,
)
from django_apps.shapez_asteroid.optimization.incremental_commit import commit_best_genome
from django_apps.shapez_asteroid.optimization.optimization_replay import OptimizationReplayRecorder
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)
from django_apps.shapez_asteroid.optimization.route_probe import run_route_probe

from .fixtures.narrow_corridor import (
    build_narrow_bridge_optimization_input,
    build_rim_competition_pool,
    narrow_bridge_coords,
)


def test_narrow_corridor_probe_vs_commit_regression() -> None:
    """Candidate pool snapshots show reachability; commit-time probe rolls back the second rim."""

    inp, _goal = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    left, right = pool
    assert left.route_probe_result.reachable is True
    assert right.route_probe_result.reachable is True

    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    assert res.candidate_results[0].commit_state is PlacementCommitState.CONFIRMED
    assert res.candidate_results[1].commit_state is PlacementCommitState.ROLLED_BACK
    assert res.candidate_results[1].conflict_reason is CommitConflictReason.ROUTE_PROBE_FAILED


def test_shared_corridor_pressure_regression() -> None:
    """First rim locks the bridge for SHAPE; second rim cannot reach the goal (starvation)."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    assert res.confirmed_candidate_count == 1
    assert res.rolled_back_candidate_count == 1


def test_high_throughput_rim_second_rolls_back_shared_corridor_regression() -> None:
    """Commit order dominates: very high ``base_throughput`` on the second rim still rolls back."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(
        inp,
        rim_left_base_throughput=1,
        rim_right_base_throughput=50_000,
    )
    assert pool[1].base_throughput == 50_000
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    assert res.candidate_results[0].commit_state is PlacementCommitState.CONFIRMED
    assert res.candidate_results[1].commit_state is PlacementCommitState.ROLLED_BACK


def test_mixed_shape_fluid_shared_corridor_probe_reachable_commit_regression() -> None:
    """Solo pool probes reachable; first SHAPE commit reserves exit cells as shape-only trunk."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(
        inp,
        rim_left_transport_kind=TransportKind.SHAPE_BELT,
        rim_right_transport_kind=TransportKind.FLUID_PIPE,
    )
    assert all(c.route_probe_result.reachable for c in pool)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    assert res.confirmed_candidate_count == 1
    assert res.rolled_back_candidate_count == 1


def test_future_expansion_penalty_regression() -> None:
    """future_expansion_penalty breakdown contract regression.

    v0 placeholder 0; ``fitness_breakdown_total_matches_components`` holds.
    """

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    rd = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    fb = evaluate_genome(genome, pool, route_domain=rd)
    assert hasattr(fb, "future_expansion_penalty")
    assert fb.future_expansion_penalty == pytest.approx(0.0)
    assert fitness_breakdown_total_matches_components(fb) is True


def test_trunk_sharing_penalty_regression() -> None:
    """trunk_sharing_penalty breakdown contract regression.

    v0 placeholder 0; ``fitness_breakdown_total_matches_components`` holds.
    """

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    rd = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    fb = evaluate_genome(genome, pool, route_domain=rd)
    assert hasattr(fb, "trunk_sharing_penalty")
    assert fb.trunk_sharing_penalty == pytest.approx(0.0)
    assert fitness_breakdown_total_matches_components(fb) is True


def test_transport_kind_corridor_conflict_regression() -> None:
    """Mixed transport: after SHAPE trunk, stale fluid path → ``TRANSPORT_KIND_CONFLICT``.

    ``protected_bridge=False`` so the bridge cell receives the SHAPE trunk mask overlay on
    commit (protected cells skip trunk overlay — see ``RouteDomainSnapshotBuilder``).

    Synthetic regression: ``fake_probe`` below patches fluid ``run_route_probe`` only for
    this test so the conflict path is exercised without changing production probe/commit logic.
    """

    inp, goal = build_narrow_bridge_optimization_input(protected_bridge=False)
    c0, c1, c2 = narrow_bridge_coords()

    solo_path = (c1, c2)
    stale_ok = RouteProbeResult(
        reachable=True,
        path=solo_path,
        cost=len(solo_path),
        expanded_nodes=len(solo_path),
        reached_goal=goal,
        goal_priority=goal.priority,
        failure_reason=None,
    )

    def mk(cid: str, occ: frozenset, tk: TransportKind) -> BundleCandidate:
        ex = min(occ, key=lambda z: (z.x, z.y))
        ext = tuple(sorted(occ - {ex}, key=lambda z: (z.x, z.y)))
        return BundleCandidate(
            candidate_id=cid,
            pattern_id="narrow_mixed",
            topology_signature="narrow_mixed_v0",
            extractor=ex,
            extensions=ext,
            occupied_cells=occ,
            output_stub=c1,
            output_dir=CardinalDirection.EAST,
            transport_kind=tk,
            base_throughput=1,
            base_score=1.0,
            route_probe_result=stale_ok,
        )

    shape = mk("shape_rim", frozenset({c0}), TransportKind.SHAPE_BELT)
    fluid = mk("fluid_rim", frozenset({c2}), TransportKind.FLUID_PIPE)
    pool = (shape, fluid)
    genome = Genome("mixed_g", (Gene("shape_rim", True, 0), Gene("fluid_rim", True, 1)), seed=7)

    # Synthetic regression hook:
    # Force the fluid probe path through the already-reserved shape corridor
    # so commit conflict classification can be tested without changing
    # route_probe or incremental_commit production logic.
    def fake_probe(probe_inp: RouteProbeInput, *, occupied_cells=None):
        if probe_inp.transport_kind is TransportKind.SHAPE_BELT:
            return run_route_probe(probe_inp, occupied_cells=occupied_cells)
        return RouteProbeResult(
            reachable=True,
            path=(c1,),
            cost=2,
            expanded_nodes=2,
            reached_goal=goal,
            goal_priority=0,
            failure_reason=None,
        )

    with patch(
        "django_apps.shapez_asteroid.optimization.incremental_commit.run_route_probe",
        side_effect=fake_probe,
    ):
        res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)

    assert res.candidate_results[0].commit_state is PlacementCommitState.CONFIRMED
    assert res.candidate_results[1].conflict_reason is CommitConflictReason.TRANSPORT_KIND_CONFLICT


def test_replay_sink_presence_does_not_drift_evolution_or_incremental_commit() -> None:
    """Real :class:`OptimizationReplayRecorder` is output-only; same seed → same evo + commit."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, _ = build_rim_competition_pool(inp)
    rd = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = EvolutionConfig(
        seed=701,
        population_size=4,
        elite_count=1,
        mutation_rate=0.35,
        tournament_size=2,
        max_generation=4,
        max_stall_generation=0,
        time_budget_ms=None,
        forced_distant_mutation_period=None,
    )
    evo_off = run_evolutionary_search(cfg, pool, route_domain=rd, replay_recorder=None)
    rec = OptimizationReplayRecorder()
    evo_on = run_evolutionary_search(cfg, pool, route_domain=rd, replay_recorder=rec)
    assert evo_off == evo_on

    best = evo_off.best_genome
    c_off = commit_best_genome(best, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=None)
    commit_rec = OptimizationReplayRecorder()
    c_on = commit_best_genome(
        best, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=commit_rec
    )
    assert c_off == c_on


def test_replay_sink_presence_invariant_under_conservative_penalty_mode() -> None:
    """Same as ``test_replay_sink_presence_*`` but ``PenaltyMode.CONSERVATIVE`` on evolution."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, _ = build_rim_competition_pool(inp)
    rd = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = EvolutionConfig(
        seed=701,
        population_size=4,
        elite_count=1,
        mutation_rate=0.35,
        tournament_size=2,
        max_generation=4,
        max_stall_generation=0,
        time_budget_ms=None,
        forced_distant_mutation_period=None,
    )
    mode = PenaltyMode.CONSERVATIVE
    evo_off = run_evolutionary_search(
        cfg, pool, route_domain=rd, replay_recorder=None, penalty_mode=mode
    )
    rec = OptimizationReplayRecorder()
    evo_on = run_evolutionary_search(
        cfg, pool, route_domain=rd, replay_recorder=rec, penalty_mode=mode
    )
    assert evo_off == evo_on

    best = evo_off.best_genome
    c_off = commit_best_genome(best, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=None)
    commit_rec = OptimizationReplayRecorder()
    c_on = commit_best_genome(
        best, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=commit_rec
    )
    assert c_off == c_on


def test_narrow_bridge_replay_event_order_deterministic() -> None:
    """Same seed / inputs → identical replay event type sequence (output-only recorder)."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)

    def run_once() -> tuple[OptimizationReplayEventType, ...]:
        rec = OptimizationReplayRecorder()
        commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=rec)
        return tuple(f.event_type for f in rec.frames)

    a = run_once()
    b = run_once()
    assert a == b
    assert OptimizationReplayEventType.ROUTE_COMMIT_ATTEMPTED in a
    assert OptimizationReplayEventType.ROUTE_COMMITTED in a
    assert OptimizationReplayEventType.ROUTE_ROLLED_BACK in a


def test_narrow_bridge_seed_domain_prefers_protected_over_trunk_overlap() -> None:
    """When protected corridor overlaps ``existing_trunk_cells``, seed class stays narrow."""

    inp, _ = build_narrow_bridge_optimization_input(
        protected_bridge=True,
        existing_trunk_overlap=True,
    )
    c1 = narrow_bridge_coords()[1]
    assert c1 in inp.protected_corridor_cells
    assert c1 in inp.existing_trunk_cells
    dom = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    assert dom[c1].route_class is RouteClass.NARROW_CORRIDOR


def test_narrow_passage_metric_counts_protected_bridge() -> None:
    """``narrow_passage_occupied_count`` increments when solo probe paths use the bridge."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    rd = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    fb = evaluate_genome(genome, pool, route_domain=rd)
    assert fb.metrics.narrow_passage_occupied_count >= 1


def test_commit_time_probe_uses_latest_route_domain_not_stale_pool() -> None:
    """Second commit attempt must not trust pool snapshot: fresh probe sees blocked neighbor."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    ids: list[int] = []

    def capture(probe_inp: RouteProbeInput, *, occupied_cells=None):
        ids.append(id(probe_inp.route_domain))
        return run_route_probe(probe_inp, occupied_cells=occupied_cells)

    with patch(
        "django_apps.shapez_asteroid.optimization.incremental_commit.run_route_probe",
        side_effect=capture,
    ):
        commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)

    assert len(ids) == 2
    assert ids[0] != ids[1]
    right = pool[1]
    assert right.route_probe_result.reachable is True


def test_route_fragility_penalty_ranks_dual_bridge_above_single_rim() -> None:
    """Two rim bundles sharing the bridge get higher ``route_fragility_penalty`` than one."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, dual_genome = build_rim_competition_pool(inp)
    left_id, right_id = pool[0].candidate_id, pool[1].candidate_id
    single_left = Genome(
        "g_one",
        (Gene(left_id, True, 0), Gene(right_id, False, 1)),
        seed=1,
    )
    rd = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    fb_dual = evaluate_genome(
        dual_genome, pool, route_domain=rd, penalty_mode=PenaltyMode.CONSERVATIVE
    )
    fb_single = evaluate_genome(
        single_left, pool, route_domain=rd, penalty_mode=PenaltyMode.CONSERVATIVE
    )
    assert fb_dual.route_fragility_penalty > fb_single.route_fragility_penalty
    assert fb_single.total > fb_dual.total
    assert fitness_breakdown_total_matches_components(fb_dual) is True
    assert fitness_breakdown_total_matches_components(fb_single) is True


def test_conservative_shared_corridor_pressure_suppresses_high_throughput_dual() -> None:
    """Narrow shared-cell weight dominates marginal throughput gain from enabling both rims."""

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, dual_genome = build_rim_competition_pool(
        inp,
        rim_left_base_throughput=1,
        rim_right_base_throughput=50_000,
    )
    left_id, right_id = pool[0].candidate_id, pool[1].candidate_id
    right_only = Genome(
        "g_right_only",
        (Gene(left_id, False, 0), Gene(right_id, True, 1)),
        seed=3,
    )
    rd = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    fb_dual = evaluate_genome(
        dual_genome, pool, route_domain=rd, penalty_mode=PenaltyMode.CONSERVATIVE
    )
    fb_right = evaluate_genome(
        right_only, pool, route_domain=rd, penalty_mode=PenaltyMode.CONSERVATIVE
    )
    assert fb_dual.shared_corridor_pressure_penalty > 0.0
    assert fb_right.shared_corridor_pressure_penalty == 0.0
    assert fb_dual.throughput_score > fb_right.throughput_score
    assert fb_right.total > fb_dual.total
    assert fitness_breakdown_total_matches_components(fb_dual) is True
    assert fitness_breakdown_total_matches_components(fb_right) is True


def test_late_commit_probe_failure_proxy_stale_reachable_zero_unreachable() -> None:
    """Pool probes stay reachable; conservative penalties still flag dual-bridge commit risk.

    Matches ``commit_best_genome`` outcome where the second rim rolls back after reservations
    (fresh reprobe), while fitness uses only candidate-stage snapshots — no replay input.
    """

    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, dual_genome = build_rim_competition_pool(inp)
    rd = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    fb = evaluate_genome(dual_genome, pool, route_domain=rd, penalty_mode=PenaltyMode.CONSERVATIVE)
    res = commit_best_genome(dual_genome, pool, inp, RouteDomainSnapshotBuilder)

    assert fb.metrics.unreachable_count == 0
    assert all(c.route_probe_result.reachable for c in pool)
    assert res.rolled_back_candidate_count >= 1
    assert fb.route_fragility_penalty > 0.0
    assert fb.shared_corridor_pressure_penalty > 0.0
    assert fitness_breakdown_total_matches_components(fb) is True
