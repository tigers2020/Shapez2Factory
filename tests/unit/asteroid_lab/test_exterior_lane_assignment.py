"""ELCP v0 nearest-lane selection (unit only, no commit hook).

Fill-first policy lives in ``test_exterior_lane_fill_first`` /
``assign_fill_first_exterior_lane`` (ELCP-TM).
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ExteriorLaneCapacityPlan,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.commit.exterior_lane_assignment import (
    increment_assignment_state,
    initial_assignment_state,
    select_exterior_lane_for_candidate,
)
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


def test_selects_nearest_lane_by_probe_cost() -> None:
    traversable = frozenset({(0, 0), (1, 0), (2, 0), (0, 1)})
    domain = _mini_domain(traversable=traversable, blocked=frozenset({(1, 0)}))
    plan = _plan(
        _lane("exterior_lane:shape_belt:0", (1, 0)),
        _lane("exterior_lane:shape_belt:1", (0, 1)),
    )
    selection = select_exterior_lane_for_candidate(
        _candidate("c1"),
        plan=plan,
        assignment_state=initial_assignment_state(plan),
        domain=domain,
        candidate_throughput_per_min=Decimal("480"),
        probe_start=(0, 0),
        max_expansions=256,
    )
    assert selection is not None
    assert selection.lane_id == "exterior_lane:shape_belt:1"


def test_capacity_overflow_uses_second_lane() -> None:
    traversable = frozenset({(0, 0), (1, 0), (2, 0)})
    domain = _mini_domain(traversable=traversable)
    cap = Decimal("500")
    plan = _plan(
        _lane("exterior_lane:shape_belt:0", (2, 0), capacity=cap),
        _lane("exterior_lane:shape_belt:1", (1, 0), capacity=cap),
    )
    state = increment_assignment_state(
        initial_assignment_state(plan),
        lane_id="exterior_lane:shape_belt:0",
        delta=Decimal("480"),
    )
    selection = select_exterior_lane_for_candidate(
        _candidate("c2", output_stub=(0, 0)),
        plan=plan,
        assignment_state=state,
        domain=domain,
        candidate_throughput_per_min=Decimal("100"),
        probe_start=(0, 0),
        max_expansions=256,
    )
    assert selection is not None
    assert selection.lane_id == "exterior_lane:shape_belt:1"


def test_returns_none_when_no_compatible_lane_has_capacity() -> None:
    traversable = frozenset({(0, 0), (1, 0)})
    domain = _mini_domain(traversable=traversable)
    cap = Decimal("100")
    plan = _plan(_lane("exterior_lane:shape_belt:0", (1, 0), capacity=cap))
    state = increment_assignment_state(
        initial_assignment_state(plan),
        lane_id="exterior_lane:shape_belt:0",
        delta=Decimal("100"),
    )
    selection = select_exterior_lane_for_candidate(
        _candidate("c1"),
        plan=plan,
        assignment_state=state,
        domain=domain,
        candidate_throughput_per_min=Decimal("1"),
        probe_start=(0, 0),
        max_expansions=256,
    )
    assert selection is None


def test_transport_kind_mismatch_returns_none() -> None:
    traversable = frozenset({(0, 0), (1, 0)})
    domain = _mini_domain(traversable=traversable)
    plan = _plan(_lane("exterior_lane:shape_belt:0", (1, 0)))
    candidate = replace(_candidate("c1"), transport_kind=TransportKind.FLUID_PIPE)
    selection = select_exterior_lane_for_candidate(
        candidate,
        plan=plan,
        assignment_state=initial_assignment_state(plan),
        domain=domain,
        candidate_throughput_per_min=Decimal("480"),
        probe_start=(0, 0),
        max_expansions=256,
    )
    assert selection is None
