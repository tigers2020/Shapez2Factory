"""Bounded weighted route feasibility probe for Layer 03 candidates."""

from __future__ import annotations

import heapq
from collections import deque

from django_apps.asteroid_lab.layers.contracts.candidates import (
    BundleCandidate,
    CandidateRejectReason,
    RouteProbedBundleCandidate,
    RouteProbeResult,
    RouteProbeStatus,
)
from django_apps.asteroid_lab.layers.contracts.route_goal import RouteGoal
from django_apps.asteroid_lab.layers.contracts.weighted_transport_route_domain import (
    WeightedTransportRouteDomain,
)
from django_apps.asteroid_lab.snapshots.grid_contract import Coord, neighbors4

LAYER03_ROUTE_PROBE_MAX_PATH_CELLS = 64
LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES = 512
LAYER03_ROUTE_PROBE_MAX_STEPS = LAYER03_ROUTE_PROBE_MAX_PATH_CELLS


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct_path(parent: dict[Coord, Coord | None], goal: Coord) -> tuple[Coord, ...]:
    path: list[Coord] = []
    current: Coord | None = goal
    while current is not None:
        path.append(current)
        current = parent.get(current)
    path.reverse()
    return tuple(path)


def _field_cells_on_path(path: tuple[Coord, ...], *, field_cells: frozenset[Coord]) -> int:
    return sum(1 for coord in path[1:] if coord in field_cells)


def weighted_route_probe(
    *,
    candidate: BundleCandidate,
    route_goals: tuple[RouteGoal, ...],
    domain: WeightedTransportRouteDomain,
    field_cells: frozenset[Coord],
) -> RouteProbedBundleCandidate:
    matching = [g for g in route_goals if g.transport_kind == candidate.transport_kind]
    if not matching:
        return RouteProbedBundleCandidate(
            candidate=candidate,
            route_probe_status=RouteProbeStatus.FAILED,
            route_probe_result=None,
            route_goal_id=None,
            reject_reason=CandidateRejectReason.ROUTE_PROBE_FAILED,
        )

    start = candidate.route_probe_start_coord
    if domain.step_cost(start) is None:
        return RouteProbedBundleCandidate(
            candidate=candidate,
            route_probe_status=RouteProbeStatus.FAILED,
            route_probe_result=None,
            route_goal_id=None,
            reject_reason=CandidateRejectReason.EXTERIOR_ENTRY_NOT_REACHABLE,
        )

    dist_cost: dict[Coord, int] = {start: 0}
    parent: dict[Coord, Coord | None] = {start: None}
    heap: list[tuple[int, Coord]] = [(0, start)]
    expanded = 0
    goal_coords = {g.coord for g in matching}

    best_goal: tuple[int, int, int, str, Coord, tuple[Coord, ...]] | None = None

    while heap and expanded < LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES:
        cost, current = heapq.heappop(heap)
        if dist_cost.get(current) != cost:
            continue
        expanded += 1

        if current in goal_coords:
            path = _reconstruct_path(parent, current)
            if len(path) <= LAYER03_ROUTE_PROBE_MAX_PATH_CELLS:
                goal = next(g for g in matching if g.coord == current)
                candidate_tuple = (
                    cost,
                    goal.priority,
                    len(path),
                    goal.goal_id,
                    current,
                    path,
                )
                if best_goal is None or candidate_tuple < (
                    best_goal[0],
                    best_goal[1],
                    best_goal[2],
                    best_goal[3],
                ):
                    best_goal = candidate_tuple

        for neighbor in neighbors4(current):
            step = domain.step_cost(neighbor)
            if step is None:
                continue
            new_cost = cost + step
            if neighbor in dist_cost and new_cost >= dist_cost[neighbor]:
                continue
            dist_cost[neighbor] = new_cost
            parent[neighbor] = current
            heapq.heappush(heap, (new_cost, neighbor))

    if best_goal is None:
        return RouteProbedBundleCandidate(
            candidate=candidate,
            route_probe_status=RouteProbeStatus.FAILED,
            route_probe_result=None,
            route_goal_id=None,
            reject_reason=CandidateRejectReason.EXTERIOR_CONNECTOR_UNREACHABLE,
        )

    total_cost, _priority, steps, goal_id, goal_coord, path = best_goal
    if len(path) != len(frozenset(path)):
        msg = "path_coords must be a simple path (no repeated cells)"
        raise ValueError(msg)

    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=RouteProbeResult(
            reached_goal=True,
            goal_coord=goal_coord,
            path_coords=path,
            steps_expanded=steps,
            transport_kind=candidate.transport_kind,
            route_cost=total_cost,
            field_route_cell_count=_field_cells_on_path(path, field_cells=field_cells),
        ),
        route_goal_id=goal_id,
        reject_reason=None,
    )


def immediate_route_probe(
    *,
    candidate: BundleCandidate,
    route_goals: tuple[RouteGoal, ...],
    placeable_cells: frozenset[Coord],
) -> RouteProbedBundleCandidate:
    matching = [g for g in route_goals if g.transport_kind == candidate.transport_kind]
    if not matching:
        return RouteProbedBundleCandidate(
            candidate=candidate,
            route_probe_status=RouteProbeStatus.FAILED,
            route_probe_result=None,
            route_goal_id=None,
            reject_reason=CandidateRejectReason.ROUTE_PROBE_FAILED,
        )

    start = candidate.route_probe_start_coord
    if start not in placeable_cells:
        return RouteProbedBundleCandidate(
            candidate=candidate,
            route_probe_status=RouteProbeStatus.FAILED,
            route_probe_result=None,
            route_goal_id=None,
            reject_reason=CandidateRejectReason.EXTERIOR_ENTRY_NOT_REACHABLE,
        )

    parent: dict[Coord, Coord | None] = {start: None}
    distance: dict[Coord, int] = {start: 0}
    queue: deque[Coord] = deque([start])

    while queue:
        current = queue.popleft()
        dist = distance[current]
        if dist >= LAYER03_ROUTE_PROBE_MAX_PATH_CELLS:
            continue
        for neighbor in neighbors4(current):
            if neighbor not in placeable_cells or neighbor in distance:
                continue
            distance[neighbor] = dist + 1
            parent[neighbor] = current
            queue.append(neighbor)

    reachable_goals: list[tuple[int, int, str, Coord, tuple[Coord, ...]]] = []
    for goal in matching:
        if goal.coord not in distance:
            continue
        dist_steps = distance[goal.coord]
        reachable_goals.append(
            (
                goal.priority,
                dist_steps,
                goal.goal_id,
                goal.coord,
                _reconstruct_path(parent, goal.coord),
            ),
        )

    if not reachable_goals:
        return RouteProbedBundleCandidate(
            candidate=candidate,
            route_probe_status=RouteProbeStatus.FAILED,
            route_probe_result=None,
            route_goal_id=None,
            reject_reason=CandidateRejectReason.EXTERIOR_CONNECTOR_UNREACHABLE,
        )

    _priority, _steps, goal_id, goal_coord, path = min(reachable_goals)
    if len(path) != len(frozenset(path)):
        msg = "path_coords must be a simple path (no repeated cells)"
        raise ValueError(msg)
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=RouteProbeResult(
            reached_goal=True,
            goal_coord=goal_coord,
            path_coords=path,
            steps_expanded=_steps,
            transport_kind=candidate.transport_kind,
        ),
        route_goal_id=goal_id,
        reject_reason=None,
    )


__all__ = [
    "LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES",
    "LAYER03_ROUTE_PROBE_MAX_PATH_CELLS",
    "LAYER03_ROUTE_PROBE_MAX_STEPS",
    "immediate_route_probe",
    "weighted_route_probe",
]
