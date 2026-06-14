"""Bounded weighted route feasibility probe for Layer 03 candidates."""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    BundleCandidate,
    CandidateRejectReason,
    RouteProbedBundleCandidate,
    RouteProbeResult,
    RouteProbeStatus,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_domain_snapshot_builder import (  # noqa: E501
    RouteDomainSnapshotBuilder,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import RouteGoal
from shapez2_factory.application.asteroid_lab.layers.contracts.route_probe_diagnostic import (
    classify_exterior_goal_unreachable,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.weighted_transport_route_domain import (  # noqa: E501
    WeightedTransportRouteDomain,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import (
    BBox,
    Coord,
    neighbors4,
)

LAYER03_ROUTE_PROBE_MIN_PATH_CELLS = 64
LAYER03_ROUTE_PROBE_MAX_PATH_CELLS_CAP = 512
LAYER03_ROUTE_PROBE_MIN_EXPANDED_NODES = 512
LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES_CAP = 4096
LAYER03_ROUTE_PROBE_MAX_PATH_CELLS = LAYER03_ROUTE_PROBE_MIN_PATH_CELLS
LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES = LAYER03_ROUTE_PROBE_MIN_EXPANDED_NODES
LAYER03_ROUTE_PROBE_MAX_STEPS = LAYER03_ROUTE_PROBE_MAX_PATH_CELLS


@dataclass(frozen=True, slots=True)
class RouteProbeLimits:
    max_path_cells: int
    max_expanded_nodes: int


def resolve_layer03_route_probe_limits(*, search_bbox: BBox) -> RouteProbeLimits:
    """Scale Phase B probe budget so rim stubs can reach exterior goals on large maps."""

    span_x = search_bbox.max_x - search_bbox.min_x + 1
    span_y = search_bbox.max_y - search_bbox.min_y + 1
    manhattan_span = span_x + span_y
    max_path = max(
        LAYER03_ROUTE_PROBE_MIN_PATH_CELLS,
        min(LAYER03_ROUTE_PROBE_MAX_PATH_CELLS_CAP, manhattan_span * 4),
    )
    max_expanded = max(
        LAYER03_ROUTE_PROBE_MIN_EXPANDED_NODES,
        min(LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES_CAP, max_path * 16),
    )
    return RouteProbeLimits(max_path_cells=max_path, max_expanded_nodes=max_expanded)


def _limits_or_default(probe_limits: RouteProbeLimits | None) -> RouteProbeLimits:
    if probe_limits is not None:
        return probe_limits
    return RouteProbeLimits(
        max_path_cells=LAYER03_ROUTE_PROBE_MAX_PATH_CELLS,
        max_expanded_nodes=LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES,
    )


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


def _stub_coord_for(candidate: BundleCandidate) -> Coord:
    if candidate.transport_stub_cells:
        return min(candidate.transport_stub_cells)
    return candidate.route_probe_start_coord


def _resolve_external_void_cells(
    domain: WeightedTransportRouteDomain,
    external_void_cells: frozenset[Coord] | None,
) -> frozenset[Coord]:
    if external_void_cells is not None:
        return external_void_cells
    return frozenset(domain.walkable_cells - domain.field_cost_cells)


def _failed_probe(
    *,
    candidate: BundleCandidate,
    matching: tuple[RouteGoal, ...],
    domain: WeightedTransportRouteDomain,
    external_void_cells: frozenset[Coord],
    visited_count: int,
    max_depth_reached: int,
    frontier_exhausted: bool,
    probe_limit_hit: bool,
    max_path_cells: int,
) -> RouteProbedBundleCandidate:
    reason, diagnostic = classify_exterior_goal_unreachable(
        anchor_coord=candidate.anchor_coord,
        stub_coord=_stub_coord_for(candidate),
        output_dir=candidate.output_dir.value,
        transport_kind=candidate.transport_kind,
        probe_start=candidate.route_probe_start_coord,
        stub_cells=candidate.transport_stub_cells,
        matching_goals=matching,
        walkable_cells=domain.walkable_cells,
        external_void_cells=external_void_cells,
        bfs_limit=max_path_cells,
        visited_count=visited_count,
        max_depth_reached=max_depth_reached,
        frontier_exhausted=frontier_exhausted,
        probe_limit_hit=probe_limit_hit,
    )
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.FAILED,
        route_probe_result=None,
        route_goal_id=None,
        reject_reason=reason,
        route_probe_diagnostic=diagnostic,
    )


def weighted_route_probe(
    *,
    candidate: BundleCandidate,
    route_goals: tuple[RouteGoal, ...],
    domain: WeightedTransportRouteDomain,
    field_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord] | None = None,
    probe_limits: RouteProbeLimits | None = None,
) -> RouteProbedBundleCandidate:
    limits = _limits_or_default(probe_limits)
    max_path_cells = limits.max_path_cells
    max_expanded_nodes = limits.max_expanded_nodes
    matching = tuple(g for g in route_goals if g.transport_kind == candidate.transport_kind)
    void_cells = _resolve_external_void_cells(domain, external_void_cells)
    if not matching:
        return _failed_probe(
            candidate=candidate,
            matching=matching,
            domain=domain,
            external_void_cells=void_cells,
            visited_count=0,
            max_depth_reached=0,
            frontier_exhausted=True,
            probe_limit_hit=False,
            max_path_cells=max_path_cells,
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
    max_depth = 0

    best_goal: tuple[int, int, int, str, Coord, tuple[Coord, ...]] | None = None

    while heap and expanded < max_expanded_nodes:
        cost, current = heapq.heappop(heap)
        if dist_cost.get(current) != cost:
            continue
        expanded += 1
        max_depth = max(max_depth, cost)

        if current in goal_coords:
            path = _reconstruct_path(parent, current)
            if len(path) <= max_path_cells:
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

    if best_goal is not None:
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

    probe_limit_hit = bool(heap) and expanded >= max_expanded_nodes
    frontier_exhausted = not heap
    return _failed_probe(
        candidate=candidate,
        matching=matching,
        domain=domain,
        external_void_cells=void_cells,
        visited_count=len(dist_cost),
        max_depth_reached=max_depth,
        frontier_exhausted=frontier_exhausted,
        probe_limit_hit=probe_limit_hit,
        max_path_cells=max_path_cells,
    )


def immediate_route_probe(
    *,
    candidate: BundleCandidate,
    route_goals: tuple[RouteGoal, ...],
    placeable_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord] | None = None,
    probe_limits: RouteProbeLimits | None = None,
) -> RouteProbedBundleCandidate:
    limits = _limits_or_default(probe_limits)
    max_path_cells = limits.max_path_cells
    matching = tuple(g for g in route_goals if g.transport_kind == candidate.transport_kind)
    void_cells = (
        external_void_cells
        if external_void_cells is not None
        else frozenset(cell for cell in placeable_cells)
    )
    domain = RouteDomainSnapshotBuilder.build_immediate_probe_surface(
        placeable_cells=placeable_cells,
    )
    if not matching:
        return _failed_probe(
            candidate=candidate,
            matching=matching,
            domain=domain,
            external_void_cells=void_cells,
            visited_count=0,
            max_depth_reached=0,
            frontier_exhausted=True,
            probe_limit_hit=False,
            max_path_cells=max_path_cells,
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
    max_depth = 0
    probe_limit_hit = False

    while queue:
        current = queue.popleft()
        dist = distance[current]
        max_depth = max(max_depth, dist)
        if dist >= max_path_cells:
            probe_limit_hit = True
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

    if reachable_goals:
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

    frontier_exhausted = not probe_limit_hit
    return _failed_probe(
        candidate=candidate,
        matching=matching,
        domain=domain,
        external_void_cells=void_cells,
        visited_count=len(distance),
        max_depth_reached=max_depth,
        frontier_exhausted=frontier_exhausted,
        probe_limit_hit=probe_limit_hit,
        max_path_cells=max_path_cells,
    )


__all__ = [
    "LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES",
    "LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES_CAP",
    "LAYER03_ROUTE_PROBE_MAX_PATH_CELLS",
    "LAYER03_ROUTE_PROBE_MAX_PATH_CELLS_CAP",
    "LAYER03_ROUTE_PROBE_MAX_STEPS",
    "LAYER03_ROUTE_PROBE_MIN_EXPANDED_NODES",
    "LAYER03_ROUTE_PROBE_MIN_PATH_CELLS",
    "RouteProbeLimits",
    "immediate_route_probe",
    "resolve_layer03_route_probe_limits",
    "weighted_route_probe",
]
