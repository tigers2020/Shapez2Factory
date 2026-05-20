"""Candidate selection tests (Solver Runtime PR4)."""

from __future__ import annotations

from dataclasses import replace

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
        extractor=(0, 0),
        extensions=(),
        occupied_cells=frozenset({(0, 0)}),
        route_probe_start=(2, 0),
        fixed_output_transport=(1, 0),
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
    )
    low = _gene_candidate(
        candidate_id="b:low",
        base_throughput=4,
        cost=10,
        goal_priority=10,
        reached_goal=goal,
    )

    plan = select_gene_candidates_greedy((low, high), inp=inp)

    assert plan.ordered_candidate_ids[0] == "a:high"


def test_candidate_selector_prefers_alternate_trunk_when_goal_saturated() -> None:
    """OD-3 v1: overflow-on-goal candidates skipped when another trunk is available."""
    goal_a = _goal((6, 0))
    goal_b = _goal((8, 0))
    inp = _minimal_inp(goals=frozenset({goal_a, goal_b}))
    saturate_a = _gene_candidate(
        candidate_id="a:saturate",
        base_throughput=16,
        cost=1,
        goal_priority=10,
        reached_goal=goal_a,
    )
    to_a = _gene_candidate(
        candidate_id="b:to_a",
        base_throughput=8,
        cost=1,
        goal_priority=10,
        reached_goal=goal_a,
    )
    to_b = _gene_candidate(
        candidate_id="c:to_b",
        base_throughput=8,
        cost=1,
        goal_priority=10,
        reached_goal=goal_b,
    )

    plan = select_gene_candidates_greedy((to_b, to_a, saturate_a), inp=inp)

    assert plan.ordered_candidate_ids[0] == "c:to_b"
    assert plan.ordered_candidate_ids[1] == "b:to_a"
    assert plan.ordered_candidate_ids[2] == "a:saturate"


def test_candidate_selector_hard_rejects_only_when_all_trunks_overflow() -> None:
    goal = _goal((6, 0))
    inp = _minimal_inp(goals=frozenset({goal}))
    heavy = _gene_candidate(
        candidate_id="a:heavy",
        base_throughput=16,
        cost=1,
        goal_priority=10,
        reached_goal=goal,
    )
    light = _gene_candidate(
        candidate_id="b:light",
        base_throughput=14,
        cost=1,
        goal_priority=10,
        reached_goal=goal,
    )

    plan = select_gene_candidates_greedy((heavy, light), inp=inp)

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
    )
    c2 = _gene_candidate(
        candidate_id="a:2",
        base_throughput=12,
        cost=4,
        goal_priority=10,
        reached_goal=goal,
    )
    c3 = _gene_candidate(
        candidate_id="m:3",
        base_throughput=4,
        cost=2,
        goal_priority=10,
        reached_goal=goal,
    )

    pool_a = (c1, c2, c3)
    pool_b = (c3, c1, c2)
    plan_a = select_gene_candidates_greedy(pool_a, inp=inp)
    plan_b = select_gene_candidates_greedy(pool_b, inp=inp)
    plan_a2 = select_gene_candidates_greedy(pool_a, inp=inp)

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
        goal_assigned_platforms={(goal.coord, TransportKind.SHAPE_BELT): 16},
    )

    assert loaded.trunk_load_penalty > empty.trunk_load_penalty
    assert loaded.total < empty.total
