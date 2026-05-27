"""ELCP-TM fill-first exterior lane assignment (unit only)."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    ExteriorLaneCapacityPlan,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.commit.exterior_lane_assignment import (
    increment_assignment_state,
    initial_assignment_state,
)
from django_apps.asteroid_lab.optimization.commit.exterior_lane_fill_first import (
    FillFirstExteriorLaneResult,
    assign_fill_first_exterior_lane,
)
from django_apps.asteroid_lab.optimization.commit.exterior_lane_trunk import initial_trunk_states
from django_apps.asteroid_lab.optimization.input_contracts import (
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import RouteCellDomain


def _goal(coord: tuple[int, int], *, priority: int = 20) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=priority,
        existing_trunk=False,
    )


def _lane(
    lane_id: str,
    coord: tuple[int, int],
    *,
    capacity: Decimal = Decimal("2880"),
    priority: int = 20,
) -> ExteriorTransportLane:
    goal = _goal(coord, priority=priority)
    return ExteriorTransportLane(
        lane_id=lane_id,
        transport_kind=TransportKind.SHAPE_BELT,
        connector_goal=goal,
        capacity_per_min=capacity,
        target_load_per_min=capacity,
        anchor_coord=coord,
    )


def _plan(*lanes: ExteriorTransportLane) -> ExteriorLaneCapacityPlan:
    cap = lanes[0].capacity_per_min if lanes else Decimal("2880")
    return ExteriorLaneCapacityPlan(
        transport_kind=TransportKind.SHAPE_BELT,
        max_asteroid_throughput_per_min=cap * len(lanes),
        lane_capacity_per_min=cap,
        required_lane_count=len(lanes),
        lanes=lanes,
    )


def _mini_domain(
    *,
    traversable: frozenset[tuple[int, int]],
    blocked: frozenset[tuple[int, int]] = frozenset(),
) -> RouteCellDomain:
    return RouteCellDomain(
        blocked_cells=blocked,
        trunk_mask_cells=frozenset({(0, 0)}),
        lift_edges=(),
        traversable_cells=traversable,
        step_costs=frozenset(),
    )


def _lin_e_pattern() -> BundlePattern:
    for pattern in build_pattern_library():
        if pattern.pattern_id == "lin_e_len0":
            return pattern
    msg = "lin_e_len0 not found"
    raise AssertionError(msg)


def _candidate(
    candidate_id: str,
    *,
    output_stub: tuple[int, int] = (0, 0),
    throughput_factor: int = 4,
) -> BundleCandidate:
    pattern = _lin_e_pattern()
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=(0, 0),
        pattern=pattern,
        output_stub=output_stub,
        output_dir=pattern.output_dir,
        occupied_cells=frozenset({(0, 0)}),
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=throughput_factor,
        route_probe_cost=5,
        reachable=True,
    )


def test_lane0_capacity_reachable_selects_lane0() -> None:
    traversable = frozenset({(0, 0), (1, 0), (2, 0), (0, 1)})
    domain = _mini_domain(traversable=traversable, blocked=frozenset({(0, 1)}))
    plan = _plan(
        _lane("exterior_lane:shape_belt:0", (1, 0)),
        _lane("exterior_lane:shape_belt:1", (0, 1)),
    )
    trunk_states = initial_trunk_states(plan)
    result = assign_fill_first_exterior_lane(
        _candidate("c1"),
        plan=plan,
        assignment_state=initial_assignment_state(plan),
        trunk_states=trunk_states,
        domain=domain,
        candidate_throughput_per_min=Decimal("480"),
        probe_start=(0, 0),
        max_expansions=256,
        trigger_candidate_id="c1",
    )
    assert result is not None
    assert isinstance(result, FillFirstExteriorLaneResult)
    assert result.lane_id == "exterior_lane:shape_belt:0"
    assert result.connector_coord == (1, 0)
    assert result.activation is None
    assert result.trunk_states == trunk_states
    assert result.probe.reachable
    assert result.reached_trunk_coord is None


def test_lane0_unreachable_with_capacity_returns_none_not_lane1() -> None:
    """Fill-first must not skip to lane1 while lane0 still has capacity (blocked path)."""

    traversable = frozenset({(0, 0), (1, 0), (2, 0), (0, 1)})
    domain = _mini_domain(traversable=traversable, blocked=frozenset({(1, 0)}))
    plan = _plan(
        _lane("exterior_lane:shape_belt:0", (1, 0)),
        _lane("exterior_lane:shape_belt:1", (0, 1)),
    )
    trunk_states = initial_trunk_states(plan)
    result = assign_fill_first_exterior_lane(
        _candidate("c1"),
        plan=plan,
        assignment_state=initial_assignment_state(plan),
        trunk_states=trunk_states,
        domain=domain,
        candidate_throughput_per_min=Decimal("480"),
        probe_start=(0, 0),
        max_expansions=256,
        trigger_candidate_id="c1",
    )
    assert result is None


def test_lane0_saturated_activates_lane1_with_evidence() -> None:
    traversable = frozenset({(0, 0), (1, 0), (2, 0)})
    domain = _mini_domain(traversable=traversable)
    cap = Decimal("500")
    plan = _plan(
        _lane("exterior_lane:shape_belt:0", (2, 0), capacity=cap),
        _lane("exterior_lane:shape_belt:1", (1, 0), capacity=cap),
    )
    assignment = increment_assignment_state(
        initial_assignment_state(plan),
        lane_id="exterior_lane:shape_belt:0",
        delta=Decimal("480"),
    )
    trunk_before = initial_trunk_states(plan)
    result = assign_fill_first_exterior_lane(
        _candidate("c2", output_stub=(0, 0)),
        plan=plan,
        assignment_state=assignment,
        trunk_states=trunk_before,
        domain=domain,
        candidate_throughput_per_min=Decimal("100"),
        probe_start=(0, 0),
        max_expansions=256,
        trigger_candidate_id="c2",
    )
    assert result is not None
    assert result.lane_id == "exterior_lane:shape_belt:1"
    assert result.activation is not None
    assert result.activation.activation_reason == ACTIVATION_REASON_CAPACITY_EXHAUSTED
    assert result.activation.activated_lane_id == "exterior_lane:shape_belt:1"
    assert result.activation.previous_lane_id == "exterior_lane:shape_belt:0"
    assert result.activation.trigger_candidate_id == "c2"
    assert result.trunk_states != trunk_before
    lane1_after = next(s for s in result.trunk_states if s.lane_id == "exterior_lane:shape_belt:1")
    assert lane1_after.active is True


def test_all_lanes_saturated_returns_none() -> None:
    traversable = frozenset({(0, 0), (1, 0), (2, 0)})
    domain = _mini_domain(traversable=traversable)
    cap = Decimal("500")
    plan = _plan(
        _lane("exterior_lane:shape_belt:0", (2, 0), capacity=cap),
        _lane("exterior_lane:shape_belt:1", (1, 0), capacity=cap),
    )
    assignment = increment_assignment_state(
        increment_assignment_state(
            initial_assignment_state(plan),
            lane_id="exterior_lane:shape_belt:0",
            delta=cap,
        ),
        lane_id="exterior_lane:shape_belt:1",
        delta=cap,
    )
    trunk_states = initial_trunk_states(plan)
    activated = tuple(
        replace(s, active=True) if s.lane_id == "exterior_lane:shape_belt:1" else s
        for s in trunk_states
    )
    result = assign_fill_first_exterior_lane(
        _candidate("c3"),
        plan=plan,
        assignment_state=assignment,
        trunk_states=activated,
        domain=domain,
        candidate_throughput_per_min=Decimal("1"),
        probe_start=(0, 0),
        max_expansions=256,
        trigger_candidate_id="c3",
    )
    assert result is None


def test_trunk_cells_goal_sets_reached_trunk_coord() -> None:
    traversable = frozenset({(0, 0), (1, 0), (2, 0)})
    domain = _mini_domain(traversable=traversable)
    plan = _plan(_lane("exterior_lane:shape_belt:0", (2, 0)))
    trunk0 = initial_trunk_states(plan)[0]
    trunk_with_cells = replace(
        trunk0,
        trunk_cells=frozenset({(1, 0)}),
        connector_coord=(2, 0),
    )
    trunk_states = (trunk_with_cells,)
    result = assign_fill_first_exterior_lane(
        _candidate("c-trunk"),
        plan=plan,
        assignment_state=initial_assignment_state(plan),
        trunk_states=trunk_states,
        domain=domain,
        candidate_throughput_per_min=Decimal("100"),
        probe_start=(0, 0),
        max_expansions=256,
        trigger_candidate_id="c-trunk",
    )
    assert result is not None
    assert result.probe.reached_goal == (1, 0)
    assert result.reached_trunk_coord == (1, 0)


def test_deterministic_tie_break_same_cost_goals() -> None:
    """When two goals tie on cost and priority, route_probe picks lower Coord."""

    traversable = frozenset({(0, 0), (1, 0), (0, 1), (2, 0), (0, 2)})
    domain = _mini_domain(traversable=traversable)
    same_priority = 20
    plan = _plan(
        _lane("exterior_lane:shape_belt:0", (2, 0), priority=same_priority),
    )
    trunk0 = initial_trunk_states(plan)[0]
    trunk_with_dual = replace(
        trunk0,
        trunk_cells=frozenset({(1, 0), (0, 1)}),
        connector_coord=(2, 0),
    )
    trunk_states = (trunk_with_dual,)
    result = assign_fill_first_exterior_lane(
        _candidate("c-tie"),
        plan=plan,
        assignment_state=initial_assignment_state(plan),
        trunk_states=trunk_states,
        domain=domain,
        candidate_throughput_per_min=Decimal("100"),
        probe_start=(0, 0),
        max_expansions=256,
        trigger_candidate_id="c-tie",
    )
    assert result is not None
    assert result.probe.cost == 1
    assert result.probe.reached_goal == (0, 1)


def test_transport_kind_mismatch_returns_none() -> None:
    traversable = frozenset({(0, 0), (1, 0)})
    domain = _mini_domain(traversable=traversable)
    plan = _plan(_lane("exterior_lane:shape_belt:0", (1, 0)))
    trunk_states = initial_trunk_states(plan)
    candidate = replace(_candidate("c1"), transport_kind=TransportKind.FLUID_PIPE)
    result = assign_fill_first_exterior_lane(
        candidate,
        plan=plan,
        assignment_state=initial_assignment_state(plan),
        trunk_states=trunk_states,
        domain=domain,
        candidate_throughput_per_min=Decimal("480"),
        probe_start=(0, 0),
        max_expansions=256,
        trigger_candidate_id="c1",
    )
    assert result is None
