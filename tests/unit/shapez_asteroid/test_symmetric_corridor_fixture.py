"""Symmetric narrow-bridge goals (post–Issue #14 hardening).

The asymmetric ``build_narrow_bridge_optimization_input`` rim_right-only goal remains in
``test_corridor_survivability_expansion.test_commit_order_right_goal_rim_first_rolls_back_then_peer_uses_bridge``.
This module fixes **dual rim goals** so ``commit_order`` alone decides bridge consumption order.
"""

from django_apps.shapez_asteroid.optimization.commit_survivability_metrics import (
    summarize_incremental_commit,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CommitConflictReason,
    OptimizationReplayEventType,
    PlacementCommitState,
)
from django_apps.shapez_asteroid.optimization.incremental_commit import commit_best_genome
from django_apps.shapez_asteroid.optimization.optimization_replay import OptimizationReplayRecorder
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)

from .fixtures import narrow_corridor as narrow_fixtures
from .fixtures.narrow_corridor import (
    build_narrow_bridge_optimization_input,
    build_symmetric_narrow_bridge_optimization_input,
    build_symmetric_rim_competition_genome,
    build_symmetric_rim_competition_pool,
    narrow_bridge_coords,
)


def test_symmetric_corridor_left_first_commits_then_right_rolls_back() -> None:
    c1 = narrow_bridge_coords()[1]
    inp, _goals = build_symmetric_narrow_bridge_optimization_input(protected_bridge=True)
    pool, _ = build_symmetric_rim_competition_pool(inp)
    genome = build_symmetric_rim_competition_genome(left_commit_order=0, right_commit_order=1)

    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    assert len(res.route_reservations) == 1
    r0 = res.route_reservations[0]
    assert r0.candidate_id == "sym_rim_left"
    assert c1 in r0.reserved_cells
    assert res.candidate_results[1].candidate_id == "sym_rim_right"
    assert res.candidate_results[1].commit_state is PlacementCommitState.ROLLED_BACK
    assert res.candidate_results[1].conflict_reason is CommitConflictReason.ROUTE_PROBE_FAILED

    m = summarize_incremental_commit(res)
    assert m.commit_attempt_count == 2
    assert m.commit_confirmed_count == 1
    assert m.commit_rolled_back_count == 1
    assert m.rollback_reason_counts == ((CommitConflictReason.ROUTE_PROBE_FAILED, 1),)


def test_symmetric_corridor_right_first_commits_then_left_rolls_back() -> None:
    c1 = narrow_bridge_coords()[1]
    inp, _ = build_symmetric_narrow_bridge_optimization_input(protected_bridge=True)
    pool, _ = build_symmetric_rim_competition_pool(inp)
    genome = build_symmetric_rim_competition_genome(left_commit_order=1, right_commit_order=0)

    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    assert res.candidate_results[0].candidate_id == "sym_rim_right"
    assert res.candidate_results[0].commit_state is PlacementCommitState.CONFIRMED
    assert c1 in res.route_reservations[0].reserved_cells

    assert res.candidate_results[1].candidate_id == "sym_rim_left"
    assert res.candidate_results[1].commit_state is PlacementCommitState.ROLLED_BACK
    assert res.candidate_results[1].conflict_reason is CommitConflictReason.ROUTE_PROBE_FAILED


def test_symmetric_corridor_replay_subsequence_is_deterministic() -> None:
    inp, _ = build_symmetric_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_symmetric_rim_competition_pool(inp)
    rec = OptimizationReplayRecorder()
    commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=rec)

    types = [f.event_type for f in rec.frames]
    first_attempt = types.index(OptimizationReplayEventType.ROUTE_COMMIT_ATTEMPTED)
    first_commit = types.index(OptimizationReplayEventType.ROUTE_COMMITTED)
    second_attempt = types.index(
        OptimizationReplayEventType.ROUTE_COMMIT_ATTEMPTED,
        first_attempt + 1,
    )
    rollback = types.index(OptimizationReplayEventType.ROUTE_ROLLED_BACK)
    summary = types.index(OptimizationReplayEventType.COMMIT_SURVIVABILITY_SUMMARY)
    assert first_attempt < first_commit < second_attempt < rollback < summary


def test_symmetric_corridor_same_seed_same_summary() -> None:
    inp, _ = build_symmetric_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_symmetric_rim_competition_pool(inp)

    def run_once() -> tuple[int, int, int, float, tuple[tuple[CommitConflictReason, int], ...]]:
        res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
        m = summarize_incremental_commit(res)
        return (
            m.commit_attempt_count,
            m.commit_confirmed_count,
            m.commit_rolled_back_count,
            m.commit_success_ratio,
            m.rollback_reason_counts,
        )

    assert run_once() == run_once()


def test_symmetric_fixture_does_not_replace_asymmetric_regression() -> None:
    """Asymmetric single-goal strip stays a separate contract; see expansion test name below."""

    inp_asym, goal = build_narrow_bridge_optimization_input(protected_bridge=True)
    assert len(inp_asym.route_goals) == 1
    assert goal.coord == narrow_bridge_coords()[2]

    inp_sym, goals = build_symmetric_narrow_bridge_optimization_input(protected_bridge=True)
    assert len(inp_sym.route_goals) == 2
    assert len(goals) == 2
    assert {g.coord for g in goals} == {narrow_bridge_coords()[0], narrow_bridge_coords()[2]}

    assert (
        narrow_fixtures.build_narrow_bridge_optimization_input
        is build_narrow_bridge_optimization_input
    )
    assert hasattr(narrow_fixtures, "build_symmetric_narrow_bridge_optimization_input")

    # Intentional cross-reference: asymmetric ordering test must remain collected.
    from . import test_corridor_survivability_expansion as exp

    names = {fn for fn in dir(exp) if fn.startswith("test_")}
    assert "test_commit_order_right_goal_rim_first_rolls_back_then_peer_uses_bridge" in names
