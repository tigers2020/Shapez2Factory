"""ELCP commit-time exterior lane selection (route_probe authoritative)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ExteriorLaneAssignmentState,
    ExteriorLaneCapacityPlan,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import RouteCellDomain
from django_apps.asteroid_lab.optimization.routing.route_probe import RouteProbeResult, probe_route


@dataclass(frozen=True, slots=True)
class ExteriorLaneSelection:
    lane_id: str
    connector_coord: Coord
    route_probe_cost: int
    probe: RouteProbeResult


def initial_assignment_state(
    plan: ExteriorLaneCapacityPlan,
) -> tuple[ExteriorLaneAssignmentState, ...]:
    return tuple(
        ExteriorLaneAssignmentState(lane_id=lane.lane_id, assigned_load_per_min=Decimal("0"))
        for lane in plan.lanes
    )


def assigned_load_by_lane_id(
    state: tuple[ExteriorLaneAssignmentState, ...],
) -> dict[str, Decimal]:
    return {row.lane_id: row.assigned_load_per_min for row in state}


def increment_assignment_state(
    state: tuple[ExteriorLaneAssignmentState, ...],
    *,
    lane_id: str,
    delta: Decimal,
) -> tuple[ExteriorLaneAssignmentState, ...]:
    return tuple(
        ExteriorLaneAssignmentState(
            lane_id=row.lane_id,
            assigned_load_per_min=row.assigned_load_per_min + delta
            if row.lane_id == lane_id
            else row.assigned_load_per_min,
        )
        for row in state
    )


def _load_ratio(
    *,
    assigned: Decimal,
    capacity: Decimal,
) -> Decimal:
    if capacity <= 0:
        return Decimal("999999")
    return assigned / capacity


def _lane_sort_key(
    *,
    lane: ExteriorTransportLane,
    probe_cost: int,
    assigned: Decimal,
) -> tuple[int, Decimal, int, Coord, str]:
    priority = lane.connector_goal.priority
    return (
        probe_cost,
        _load_ratio(assigned=assigned, capacity=lane.capacity_per_min),
        -priority,
        lane.connector_goal.coord,
        lane.lane_id,
    )


def select_exterior_lane_for_candidate(
    candidate: BundleCandidate,
    *,
    plan: ExteriorLaneCapacityPlan,
    assignment_state: tuple[ExteriorLaneAssignmentState, ...],
    domain: RouteCellDomain,
    candidate_throughput_per_min: Decimal,
    probe_start: Coord,
    max_expansions: int,
) -> ExteriorLaneSelection | None:
    """Pick nearest compatible lane with remaining capacity (commit-time route_probe cost)."""

    if candidate.transport_kind is not plan.transport_kind:
        return None

    assigned = assigned_load_by_lane_id(assignment_state)
    ranked: list[
        tuple[tuple[int, Decimal, int, Coord, str], ExteriorTransportLane, RouteProbeResult]
    ] = []

    for lane in plan.lanes:
        if lane.transport_kind != candidate.transport_kind:
            continue
        current_assigned = assigned.get(lane.lane_id, Decimal("0"))
        if current_assigned + candidate_throughput_per_min > lane.capacity_per_min:
            continue
        goal_coord = lane.connector_goal.coord
        probe = probe_route(
            domain,
            probe_start,
            frozenset({goal_coord}),
            max_expansions=max_expansions,
            goal_priority={goal_coord: lane.connector_goal.priority},
        )
        if not probe.reachable or probe.reached_goal != goal_coord:
            continue
        sort_key = _lane_sort_key(
            lane=lane,
            probe_cost=probe.cost,
            assigned=current_assigned,
        )
        ranked.append((sort_key, lane, probe))

    if not ranked:
        return None

    ranked.sort(key=lambda item: item[0])
    _, best_lane, best_probe = ranked[0]
    return ExteriorLaneSelection(
        lane_id=best_lane.lane_id,
        connector_coord=best_lane.connector_goal.coord,
        route_probe_cost=best_probe.cost,
        probe=best_probe,
    )


__all__ = [
    "ExteriorLaneSelection",
    "assigned_load_by_lane_id",
    "increment_assignment_state",
    "initial_assignment_state",
    "select_exterior_lane_for_candidate",
]
