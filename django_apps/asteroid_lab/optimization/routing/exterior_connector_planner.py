"""EVTC exterior void connector goal planner (Phase C policy, v0)."""

from __future__ import annotations

from collections import deque

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.routing.exterior_connector_plan import (
    ExteriorConnectorPlan,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.snapshots.grid_contract import neighbors4

_EXTERNAL_MARGIN_PRIORITY = 20
_OUTER_VOID_PADDING = 10
_MIN_BFS_DISTANCE = 3
_MAX_BFS_DISTANCE = 5


def _route_domain_bbox(mineable: frozenset[Coord]) -> frozenset[Coord]:
    if not mineable:
        return frozenset()
    xs = [coord[0] for coord in mineable]
    ys = [coord[1] for coord in mineable]
    min_x = min(xs) - _OUTER_VOID_PADDING
    max_x = max(xs) + _OUTER_VOID_PADDING
    min_y = min(ys) - _OUTER_VOID_PADDING
    max_y = max(ys) + _OUTER_VOID_PADDING
    return frozenset((x, y) for x in range(min_x, max_x + 1) for y in range(min_y, max_y + 1))


def _bfs_distance_from_mineable(
    mineable: frozenset[Coord],
    bbox: frozenset[Coord],
) -> dict[Coord, int]:
    distances: dict[Coord, int] = {}
    queue: deque[tuple[Coord, int]] = deque()
    for start in sorted(mineable):
        if start not in bbox:
            continue
        distances[start] = 0
        queue.append((start, 0))
    while queue:
        coord, dist = queue.popleft()
        for neighbor in neighbors4(coord):
            if neighbor not in bbox:
                continue
            if neighbor in mineable:
                continue
            next_dist = dist + 1
            if neighbor in distances and distances[neighbor] <= next_dist:
                continue
            distances[neighbor] = next_dist
            queue.append((neighbor, next_dist))
    return distances


def _connector_candidates(
    inp: OptimizationInput,
    distances: dict[Coord, int],
) -> list[Coord]:
    in_band = [
        coord
        for coord in sorted(inp.external_void_cells)
        if _MIN_BFS_DISTANCE <= distances.get(coord, 0) <= _MAX_BFS_DISTANCE
    ]
    if in_band:
        return in_band
    fallback = [coord for coord in sorted(inp.external_void_cells) if distances.get(coord, 0) >= 1]
    return fallback if fallback else sorted(inp.external_void_cells)


def _select_evenly_spaced(candidates: list[Coord], count: int) -> list[Coord]:
    if count <= 0:
        return []
    if len(candidates) <= count:
        return candidates
    if count == 1:
        return [candidates[len(candidates) // 2]]
    selected: list[Coord] = []
    last_index = -1
    for pick in range(count):
        index = round(pick * (len(candidates) - 1) / (count - 1))
        if index <= last_index:
            index = min(last_index + 1, len(candidates) - 1)
        selected.append(candidates[index])
        last_index = index
    return selected


def _route_goal(
    coord: Coord,
    *,
    transport_kind: TransportKind,
) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=transport_kind,
        priority=_EXTERNAL_MARGIN_PRIORITY,
        existing_trunk=False,
    )


def plan_exterior_connectors(
    inp: OptimizationInput,
    *,
    required_count: int,
    transport_kind: TransportKind,
    skeleton: RttpSkeleton | None = None,
) -> ExteriorConnectorPlan:
    """Select ``required_count`` exterior void connector goals (deterministic)."""

    del skeleton
    required = max(0, required_count)
    bbox = _route_domain_bbox(inp.mineable_cells)
    distances = _bfs_distance_from_mineable(inp.mineable_cells, bbox)
    candidates = _connector_candidates(inp, distances)
    selected_coords = _select_evenly_spaced(candidates, required)
    goals = tuple(_route_goal(coord, transport_kind=transport_kind) for coord in selected_coords)
    shortfall = len(goals) < required
    return ExteriorConnectorPlan(
        selected_goals=goals,
        candidate_margin_coords=frozenset(candidates),
        planner_shortfall=shortfall,
        required_count=required,
    )


__all__ = ["plan_exterior_connectors"]
