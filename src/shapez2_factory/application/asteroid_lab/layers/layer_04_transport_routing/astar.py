"""A* shortest-path search for Layer 04 (deterministic tie-break)."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import RouteGoal
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.route_domain import (  # noqa: E501
    L4RouteSearchDomain,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord, neighbors4


@dataclass(frozen=True, slots=True)
class AstarPathResult:
    path: tuple[Coord, ...]
    route_cost: int
    goal_coord: Coord
    goal_id: str


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


def astar_to_nearest_goal(
    *,
    domain: L4RouteSearchDomain,
    start: Coord,
    goals: tuple[RouteGoal, ...],
) -> AstarPathResult | None:
    if not goals:
        return None
    if domain.step_cost(start) is None:
        return None

    goal_by_coord = {g.coord: g for g in goals}
    goal_coords = frozenset(goal_by_coord)

    g_score: dict[Coord, int] = {start: 0}
    parent: dict[Coord, Coord | None] = {start: None}
    # heap: (f, g, path_len, goal_id, x, y, coord) — coord last for uniqueness
    start_h = min(_manhattan(start, g.coord) for g in goals)
    heap: list[tuple[int, int, int, str, int, int, Coord]] = [
        (start_h, 0, 1, "", start[0], start[1], start)
    ]
    best_at_goal: tuple[int, int, int, str, int, int, Coord] | None = None

    while heap:
        f_score, g_cost, path_len, _gid, _x, _y, current = heapq.heappop(heap)
        if g_score.get(current) != g_cost:
            continue

        if current in goal_coords:
            goal = goal_by_coord[current]
            candidate = (
                f_score,
                g_cost,
                path_len,
                goal.goal_id,
                current[0],
                current[1],
                current,
            )
            if best_at_goal is None or candidate < best_at_goal:
                best_at_goal = candidate

        for neighbor in neighbors4(current):
            step = domain.step_cost(neighbor)
            if step is None:
                continue
            tentative = g_cost + step
            if neighbor in g_score and tentative >= g_score[neighbor]:
                continue
            g_score[neighbor] = tentative
            parent[neighbor] = current
            h = min(_manhattan(neighbor, g.coord) for g in goals)
            new_len = path_len + 1
            gid = goal_by_coord[neighbor].goal_id if neighbor in goal_coords else ""
            heapq.heappush(
                heap,
                (tentative + h, tentative, new_len, gid, neighbor[0], neighbor[1], neighbor),
            )

    if best_at_goal is None:
        return None
    _f, route_cost, _plen, goal_id, _gx, _gy, goal_coord = best_at_goal
    path = _reconstruct_path(parent, goal_coord)
    return AstarPathResult(
        path=path,
        route_cost=route_cost,
        goal_coord=goal_coord,
        goal_id=goal_id,
    )


__all__ = ["AstarPathResult", "astar_to_nearest_goal"]
