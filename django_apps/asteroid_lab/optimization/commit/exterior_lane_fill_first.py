"""ELCP-TM fill-first exterior lane assignment (route_probe authoritative)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    ExteriorLaneActivationEvidence,
    ExteriorLaneAssignmentState,
    ExteriorLaneCapacityPlan,
    ExteriorLaneTrunkState,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.commit.exterior_lane_assignment import (
    assigned_load_by_lane_id,
)
from django_apps.asteroid_lab.optimization.commit.exterior_lane_trunk import activate_trunk_state
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import RouteCellDomain
from django_apps.asteroid_lab.optimization.routing.route_probe import RouteProbeResult, probe_route


@dataclass(frozen=True, slots=True)
class FillFirstExteriorLaneResult:
    lane_id: str
    connector_coord: Coord
    route_probe_cost: int
    probe: RouteProbeResult
    activation: ExteriorLaneActivationEvidence | None
    reached_trunk_coord: Coord | None
    trunk_states: tuple[ExteriorLaneTrunkState, ...]


def _trunk_states_by_lane_id(
    trunk_states: tuple[ExteriorLaneTrunkState, ...],
) -> dict[str, ExteriorLaneTrunkState]:
    return {row.lane_id: row for row in trunk_states}


def _reorder_trunk_states(
    *,
    plan: ExteriorLaneCapacityPlan,
    by_lane_id: dict[str, ExteriorLaneTrunkState],
) -> tuple[ExteriorLaneTrunkState, ...]:
    return tuple(by_lane_id[lane.lane_id] for lane in plan.lanes)


def _first_active_lane_index(
    *,
    plan: ExteriorLaneCapacityPlan,
    by_lane_id: dict[str, ExteriorLaneTrunkState],
) -> int | None:
    for index, lane in enumerate(plan.lanes):
        if by_lane_id[lane.lane_id].active:
            return index
    return None


def _first_active_lane_index_with_capacity(
    *,
    plan: ExteriorLaneCapacityPlan,
    by_lane_id: dict[str, ExteriorLaneTrunkState],
    assigned: dict[str, Decimal],
    candidate_throughput_per_min: Decimal,
) -> int | None:
    for index, lane in enumerate(plan.lanes):
        trunk_row = by_lane_id[lane.lane_id]
        if not trunk_row.active:
            continue
        lane_assigned = assigned.get(lane.lane_id, Decimal("0"))
        if lane_assigned + candidate_throughput_per_min > lane.capacity_per_min:
            continue
        return index
    return None


def _count_active_trunk_states(by_lane_id: dict[str, ExteriorLaneTrunkState]) -> int:
    return sum(1 for row in by_lane_id.values() if row.active)


def _first_inactive_lane_index(
    *,
    plan: ExteriorLaneCapacityPlan,
    by_lane_id: dict[str, ExteriorLaneTrunkState],
) -> int | None:
    for index, lane in enumerate(plan.lanes):
        if not by_lane_id[lane.lane_id].active:
            return index
    return None


def _probe_goals_for_trunk_state(state: ExteriorLaneTrunkState) -> frozenset[Coord]:
    if state.trunk_cells:
        return frozenset(state.trunk_cells | {state.connector_coord})
    return frozenset({state.connector_coord})


def _reached_trunk_coord(
    *,
    trunk_state: ExteriorLaneTrunkState,
    reached_goal: Coord | None,
) -> Coord | None:
    if reached_goal is None:
        return None
    if reached_goal in trunk_state.trunk_cells:
        return reached_goal
    return None


def assign_fill_first_exterior_lane(
    candidate: BundleCandidate,
    *,
    plan: ExteriorLaneCapacityPlan,
    assignment_state: tuple[ExteriorLaneAssignmentState, ...],
    trunk_states: tuple[ExteriorLaneTrunkState, ...],
    domain: RouteCellDomain,
    candidate_throughput_per_min: Decimal,
    probe_start: Coord,
    max_expansions: int,
    trigger_candidate_id: str,
) -> FillFirstExteriorLaneResult | None:
    """Fill-first exterior lane: lowest active lane with capacity, else activate next."""

    if candidate.transport_kind is not plan.transport_kind:
        return None

    assigned = assigned_load_by_lane_id(assignment_state)
    by_lane_id = _trunk_states_by_lane_id(trunk_states)
    activation: ExteriorLaneActivationEvidence | None = None
    effective_states = trunk_states

    focus_index = _first_active_lane_index_with_capacity(
        plan=plan,
        by_lane_id=by_lane_id,
        assigned=assigned,
        candidate_throughput_per_min=candidate_throughput_per_min,
    )

    if focus_index is None:
        if _count_active_trunk_states(by_lane_id) >= plan.required_lane_count:
            return None
        previous_index = _first_active_lane_index(plan=plan, by_lane_id=by_lane_id)
        if previous_index is None:
            return None
        previous_lane = plan.lanes[previous_index]
        previous_assigned = assigned.get(previous_lane.lane_id, Decimal("0"))
        if previous_assigned + candidate_throughput_per_min <= previous_lane.capacity_per_min:
            return None

        next_index = _first_inactive_lane_index(plan=plan, by_lane_id=by_lane_id)
        if next_index is None:
            return None

        next_lane = plan.lanes[next_index]
        next_trunk_before = by_lane_id[next_lane.lane_id]
        activated = activate_trunk_state(next_trunk_before)
        by_lane_id[next_lane.lane_id] = activated
        effective_states = _reorder_trunk_states(plan=plan, by_lane_id=by_lane_id)

        activation = ExteriorLaneActivationEvidence(
            activated_lane_id=next_lane.lane_id,
            previous_lane_id=previous_lane.lane_id,
            previous_lane_assigned_load_per_min=previous_assigned,
            previous_lane_capacity_per_min=previous_lane.capacity_per_min,
            trigger_candidate_id=trigger_candidate_id,
            trigger_candidate_throughput_per_min=candidate_throughput_per_min,
            activation_reason=ACTIVATION_REASON_CAPACITY_EXHAUSTED,
        )

        focus_index = next_index

    lane = plan.lanes[focus_index]
    trunk_row = by_lane_id[lane.lane_id]
    lane_assigned = assigned.get(lane.lane_id, Decimal("0"))
    if lane_assigned + candidate_throughput_per_min > lane.capacity_per_min:
        return None

    goals = _probe_goals_for_trunk_state(trunk_row)
    goal_priority = {coord: lane.connector_goal.priority for coord in goals}
    probe = probe_route(
        domain,
        probe_start,
        goals,
        max_expansions=max_expansions,
        goal_priority=goal_priority,
    )
    if not probe.reachable or probe.reached_goal is None or probe.reached_goal not in goals:
        return None

    reached_trunk = _reached_trunk_coord(
        trunk_state=trunk_row,
        reached_goal=probe.reached_goal,
    )
    return FillFirstExteriorLaneResult(
        lane_id=lane.lane_id,
        connector_coord=lane.connector_goal.coord,
        route_probe_cost=probe.cost,
        probe=probe,
        activation=activation,
        reached_trunk_coord=reached_trunk,
        trunk_states=effective_states,
    )


__all__ = [
    "FillFirstExteriorLaneResult",
    "assign_fill_first_exterior_lane",
]
