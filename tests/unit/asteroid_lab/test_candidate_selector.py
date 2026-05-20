"""Candidate selection tests (Solver Runtime PR4)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.optimization.bundle_selection_targets import (
    compute_bundle_selection_targets,
)
from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.candidate_score import (
    CORRIDOR_CELL_WEIGHT,
    GOAL_PRIORITY_WEIGHT,
    ROUTE_COST_WEIGHT,
    THROUGHPUT_WEIGHT,
    score_gene_candidate,
)
from django_apps.asteroid_lab.optimization.candidate_selector import (
    select_gene_candidates_greedy,
)
from django_apps.asteroid_lab.optimization.enums import Direction, RouteGoalKind, TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    RouteGoal,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.route_probe import RouteProbeResult


def _goal(
    coord: tuple[int, int],
    *,
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
    priority: int = 10,
) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=transport_kind,
        priority=priority,
        existing_trunk=False,
    )


def _minimal_inp(*, goals: frozenset[RouteGoal] | None = None):
    bb = BBox(0, 10, 0, 0)
    default_goals = frozenset({_goal((6, 0))})
    return replace(
        greenfield_optimization_input(bbox=bb),
        route_goals=goals if goals is not None else default_goals,
    )


def _gene_candidate(
    *,
    candidate_id: str,
    base_throughput: int,
    cost: int,
    goal_priority: int,
    reached_goal: RouteGoal,
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
    path: tuple[tuple[int, int], ...] = (),
    extractor: tuple[int, int] = (0, 0),
) -> GeneCandidate:
    probe = RouteProbeResult(
        reachable=True,
        path=path,
        cost=cost,
        expanded_nodes=1,
        reached_goal=reached_goal,
        goal_priority=goal_priority,
        failure_reason=None,
    )
    return GeneCandidate(
        candidate_id=candidate_id,
        gene_id="test_gene",
        topology_signature="sig",
        extractor=extractor,
        extensions=(),
        occupied_cells=frozenset({extractor}),
        route_probe_start=(extractor[0] + 2, extractor[1]),
        fixed_output_transport=(extractor[0] + 1, extractor[1]),
        output_dir=Direction.E,
        transport_kind=transport_kind,
        base_throughput=base_throughput,
        base_score=float(base_throughput),
        route_probe_result=probe,
    )


def test_candidate_selector_prefers_high_throughput_low_cost() -> None:
    goal = _goal((6, 0))
    inp = _minimal_inp(goals=frozenset({goal}))
    high = _gene_candidate(
        candidate_id="a:high",
        base_throughput=10,
        cost=3,
        goal_priority=10,
        reached_goal=goal,
        extractor=(0, 0),
    )
    low = _gene_candidate(
        candidate_id="b:low",
        base_throughput=4,
        cost=10,
        goal_priority=10,
        reached_goal=goal,
        extractor=(4, 0),
    )

    plan, _diag = select_gene_candidates_greedy((low, high), inp=inp)

    assert plan.ordered_candidate_ids[0] == "a:high"


def test_candidate_selector_prefers_alternate_trunk_when_goal_at_platform_cap() -> None:
    """OD-3 v1: per-goal platform cap (12) forces later picks to another trunk."""
    goal_a = _goal((6, 0))
    goal_b = _goal((8, 0))
    inp = _minimal_inp(goals=frozenset({goal_a, goal_b}))
    fill_a = tuple(
        _gene_candidate(
            candidate_id=f"a:{i}",
            base_throughput=4,
            cost=1,
            goal_priority=10,
            reached_goal=goal_a,
            extractor=(i, 0),
        )
        for i in range(12)
    )
    to_b = _gene_candidate(
        candidate_id="c:to_b",
        base_throughput=4,
        cost=99,
        goal_priority=10,
        reached_goal=goal_b,
        extractor=(20, 0),
    )

    plan, _diag = select_gene_candidates_greedy(fill_a + (to_b,), inp=inp)

    assert plan.ordered_candidate_ids[-1] == "c:to_b"
    assert len(plan.ordered_candidate_ids) == 13
    assert len([cid for cid in plan.ordered_candidate_ids if cid.startswith("a:")]) == 12


def test_candidate_selector_hard_rejects_only_when_all_trunks_overflow() -> None:
    goal = _goal((6, 0))
    inp = _minimal_inp(goals=frozenset({goal}))
    heavy = _gene_candidate(
        candidate_id="a:heavy",
        base_throughput=16,
        cost=1,
        goal_priority=10,
        reached_goal=goal,
        extractor=(0, 0),
    )
    light = _gene_candidate(
        candidate_id="b:light",
        base_throughput=14,
        cost=1,
        goal_priority=10,
        reached_goal=goal,
        extractor=(4, 0),
    )

    plan, _diag = select_gene_candidates_greedy((heavy, light), inp=inp)

    assert plan.ordered_candidate_ids == ("a:heavy", "b:light")


def test_candidate_selector_is_deterministic() -> None:
    goal = _goal((6, 0))
    inp = _minimal_inp(goals=frozenset({goal}))
    c1 = _gene_candidate(
        candidate_id="z:1",
        base_throughput=8,
        cost=5,
        goal_priority=10,
        reached_goal=goal,
        extractor=(0, 0),
    )
    c2 = _gene_candidate(
        candidate_id="a:2",
        base_throughput=12,
        cost=4,
        goal_priority=10,
        reached_goal=goal,
        extractor=(4, 0),
    )
    c3 = _gene_candidate(
        candidate_id="m:3",
        base_throughput=4,
        cost=2,
        goal_priority=10,
        reached_goal=goal,
        extractor=(8, 0),
    )

    pool_a = (c1, c2, c3)
    pool_b = (c3, c1, c2)
    plan_a, _ = select_gene_candidates_greedy(pool_a, inp=inp)
    plan_b, _ = select_gene_candidates_greedy(pool_b, inp=inp)
    plan_a2, _ = select_gene_candidates_greedy(pool_a, inp=inp)

    assert plan_a.ordered_candidate_ids == plan_b.ordered_candidate_ids
    assert plan_a.ordered_candidate_ids == plan_a2.ordered_candidate_ids


def test_score_gene_candidate_matches_phase_i_formula() -> None:
    goal = _goal((6, 0))
    inp = _minimal_inp(goals=frozenset({goal}))
    candidate = _gene_candidate(
        candidate_id="x:1",
        base_throughput=12,
        cost=7,
        goal_priority=5,
        reached_goal=goal,
        path=((2, 0), (3, 0)),
    )
    inp = replace(inp, protected_corridor_cells=frozenset({(3, 0)}))

    breakdown = score_gene_candidate(candidate, inp=inp, goal_assigned_platforms={})

    assert breakdown.throughput_term == 12 * THROUGHPUT_WEIGHT
    assert breakdown.route_cost_penalty == 7 * ROUTE_COST_WEIGHT
    assert breakdown.goal_priority_penalty == 5 * GOAL_PRIORITY_WEIGHT
    assert breakdown.corridor_pressure_penalty == 1 * CORRIDOR_CELL_WEIGHT
    assert breakdown.trunk_load_penalty == 0.0
    assert breakdown.total == (
        breakdown.throughput_term
        - breakdown.route_cost_penalty
        - breakdown.goal_priority_penalty
        - breakdown.corridor_pressure_penalty
        - breakdown.trunk_load_penalty
    )


def test_selector_limits_one_variant_per_extractor() -> None:
    goal = _goal((6, 0))
    inp = _minimal_inp(goals=frozenset({goal}))
    candidates = tuple(
        _gene_candidate(
            candidate_id=f"v:{i}",
            base_throughput=16 - i,
            cost=i,
            goal_priority=10,
            reached_goal=goal,
            extractor=(0, 0),
        )
        for i in range(3)
    )

    plan, diag = select_gene_candidates_greedy(candidates, inp=inp)

    assert plan.ordered_candidate_ids == ("v:0",)
    assert diag.selection_skipped_duplicate_anchor_count == 2


def test_selector_anchor_diversity_preserves_best_per_anchor() -> None:
    goal = _goal((6, 0))
    inp = _minimal_inp(goals=frozenset({goal}))
    anchor_a = (
        _gene_candidate(
            candidate_id="a:high",
            base_throughput=16,
            cost=1,
            goal_priority=10,
            reached_goal=goal,
            extractor=(0, 0),
        ),
        _gene_candidate(
            candidate_id="a:low",
            base_throughput=8,
            cost=1,
            goal_priority=10,
            reached_goal=goal,
            extractor=(0, 0),
        ),
    )
    anchor_b = (
        _gene_candidate(
            candidate_id="b:high",
            base_throughput=14,
            cost=2,
            goal_priority=10,
            reached_goal=goal,
            extractor=(8, 0),
        ),
        _gene_candidate(
            candidate_id="b:low",
            base_throughput=6,
            cost=2,
            goal_priority=10,
            reached_goal=goal,
            extractor=(8, 0),
        ),
    )

    plan, diag = select_gene_candidates_greedy(anchor_a + anchor_b, inp=inp)

    assert set(plan.ordered_candidate_ids) == {"a:high", "b:high"}
    assert diag.selection_skipped_duplicate_anchor_count == 2


def test_selector_allows_multiple_bundles_per_goal_when_throughput_high() -> None:
    goal = _goal((6, 0))
    inp = _minimal_inp(goals=frozenset({goal}))
    candidates = tuple(
        _gene_candidate(
            candidate_id=f"m:{i}",
            base_throughput=16,
            cost=i,
            goal_priority=10,
            reached_goal=goal,
            extractor=(i * 4, 0),
        )
        for i in range(5)
    )

    plan, _diag = select_gene_candidates_greedy(candidates, inp=inp)

    assert len(plan.ordered_candidate_ids) == 5


def test_selector_ordered_count_can_exceed_route_out_count() -> None:
    goals = frozenset({_goal((6, 0)), _goal((8, 0))})
    inp = _minimal_inp(goals=goals)
    pool: list = []
    for goal in sorted(goals, key=lambda g: g.coord):
        for i in range(4):
            pool.append(
                _gene_candidate(
                    candidate_id=f"{goal.coord[0]}:{i}",
                    base_throughput=16,
                    cost=i,
                    goal_priority=10,
                    reached_goal=goal,
                    extractor=(goal.coord[0] + i, 0),
                )
            )

    plan, _diag = select_gene_candidates_greedy(tuple(pool), inp=inp)

    assert len(plan.ordered_candidate_ids) > len(goals)


def test_select_gene_candidates_does_not_mutate_optimization_input() -> None:
    goal = _goal((6, 0))
    inp = _minimal_inp(goals=frozenset({goal}))
    before_goals = inp.route_goals
    before_corridor = inp.protected_corridor_cells
    candidate = _gene_candidate(
        candidate_id="x:1",
        base_throughput=8,
        cost=1,
        goal_priority=10,
        reached_goal=goal,
    )

    select_gene_candidates_greedy((candidate,), inp=inp)

    assert inp.route_goals == before_goals
    assert inp.protected_corridor_cells == before_corridor


def test_selector_stops_when_cumulative_throughput_reaches_target() -> None:
    goals = frozenset(_goal((x * 2, 0)) for x in range(7))
    inp = _minimal_inp(goals=goals)
    targets = compute_bundle_selection_targets(goals)
    assert targets.target_miner_bundle_count == 84

    pool = tuple(
        _gene_candidate(
            candidate_id=f"m:{i}",
            base_throughput=16,
            cost=1,
            goal_priority=10,
            reached_goal=_goal((6, 0)),
            extractor=(i * 4, 0),
        )
        for i in range(20)
    )

    plan, diag = select_gene_candidates_greedy(pool, inp=inp, targets=targets)

    assert diag.selection_stopped_by_throughput_budget is True
    assert diag.selected_throughput_at_stop >= targets.target_miner_bundle_count
    assert len(plan.ordered_candidate_ids) == 6
    assert diag.selected_throughput_at_stop == 96


def test_selector_does_not_select_all_pool_when_throughput_budget_low() -> None:
    """Regression: many pool anchors must not all be selected when target is 84 tp."""

    goals = frozenset(_goal((x * 2, 0)) for x in range(7))
    inp = _minimal_inp(goals=goals)
    targets = compute_bundle_selection_targets(goals)
    assert targets.target_miner_bundle_count == 84

    pool = tuple(
        _gene_candidate(
            candidate_id=f"a{x}:{i}",
            base_throughput=16,
            cost=1,
            goal_priority=10,
            reached_goal=_goal((x * 2, 0)),
            extractor=(x * 10 + i, 0),
        )
        for x in range(7)
        for i in range(3)
    )

    plan, diag = select_gene_candidates_greedy(pool, inp=inp, targets=targets)

    assert len(pool) == 21
    assert len(plan.ordered_candidate_ids) <= 7
    assert diag.selection_stopped_by_throughput_budget is True
    assert diag.selected_throughput_at_stop >= 84


def test_selector_cap_uses_target_bundle_count_not_route_out_count() -> None:
    """Selector cap is target_miner_bundle_count (84), not route_out_count (7).

    Invariant: len(ordered) == min(len(pool), targets.target_miner_bundle_count).
    This proves that "7 routes → 7 miners" must be a generation-pool problem,
    not a selector capping problem.
    """
    route_out_count = 7
    goals = frozenset(_goal((x * 2, 0)) for x in range(route_out_count))
    inp = _minimal_inp(goals=goals)
    targets = compute_bundle_selection_targets(goals)

    assert targets.route_out_count == route_out_count
    assert targets.target_miner_bundle_count == route_out_count * 12  # 84

    pool_candidates: list[GeneCandidate] = []
    for gi, goal in enumerate(sorted(goals, key=lambda g: g.coord)):
        for i in range(2):
            pool_candidates.append(
                _gene_candidate(
                    candidate_id=f"g{goal.coord[0]}:{i}",
                    base_throughput=4,
                    cost=i + 1,
                    goal_priority=10,
                    reached_goal=goal,
                    extractor=(gi * 10 + i, 0),
                )
            )

    assert len(pool_candidates) == 14

    plan, _diag = select_gene_candidates_greedy(
        tuple(pool_candidates), inp=inp, targets=targets
    )

    assert len(plan.ordered_candidate_ids) == min(
        len(pool_candidates), targets.target_miner_bundle_count
    )  # 14 — pool exhausted before cap
    assert len(plan.ordered_candidate_ids) > route_out_count  # 14 > 7


def test_trunk_load_penalty_increases_with_assigned_platforms() -> None:
    goal = _goal((6, 0))
    inp = _minimal_inp(goals=frozenset({goal}))
    candidate = _gene_candidate(
        candidate_id="x:1",
        base_throughput=8,
        cost=1,
        goal_priority=10,
        reached_goal=goal,
    )
    empty = score_gene_candidate(candidate, inp=inp, goal_assigned_platforms={})
    loaded = score_gene_candidate(
        candidate,
        inp=inp,
        goal_assigned_platforms={(goal.coord, TransportKind.SHAPE_BELT): 8},
    )

    assert loaded.trunk_load_penalty > empty.trunk_load_penalty
    assert loaded.total < empty.total
