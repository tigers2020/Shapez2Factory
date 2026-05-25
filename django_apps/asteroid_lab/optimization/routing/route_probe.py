"""Bounded route feasibility probe on skeleton-aware route domain (PR-3)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import RouteCellDomain
from django_apps.asteroid_lab.snapshots.grid_contract import neighbors4


@dataclass(frozen=True, slots=True)
class RouteProbeResult:
    reachable: bool
    cost: int
    reached_goal: Coord | None
    path: tuple[Coord, ...]
    expanded_nodes: int


def initial_phase(domain: RouteCellDomain, start: Coord) -> str | None:
    if any(edge.platform_coord == start for edge in domain.lift_edges):
        return "platform"
    if start in domain.traversable_cells:
        return "trunk"
    return None


def probe_route(
    domain: RouteCellDomain,
    start: Coord,
    goals: frozenset[Coord],
    *,
    max_expansions: int = 500,
) -> RouteProbeResult:
    """BFS from ``start`` via optional lift edge into trunk mask / goals."""

    if not goals:
        return RouteProbeResult(
            reachable=False,
            cost=0,
            reached_goal=None,
            path=(),
            expanded_nodes=0,
        )

    if start in goals:
        return RouteProbeResult(
            reachable=True,
            cost=0,
            reached_goal=start,
            path=(start,),
            expanded_nodes=0,
        )

    phase = initial_phase(domain, start)
    if phase is None or start in domain.blocked_cells:
        return RouteProbeResult(
            reachable=False,
            cost=0,
            reached_goal=None,
            path=(),
            expanded_nodes=0,
        )

    queue: deque[tuple[Coord, str, int]] = deque([(start, phase, 0)])
    visited: set[tuple[Coord, str]] = {(start, phase)}
    parent: dict[tuple[Coord, str], tuple[Coord, str] | None] = {(start, phase): None}
    expanded = 0

    best_goal: Coord | None = None
    best_state: tuple[Coord, str] | None = None
    best_cost = 0

    while queue and expanded < max_expansions:
        coord, current_phase, cost = queue.popleft()
        expanded += 1

        if current_phase == "trunk" and coord in goals:
            if best_goal is None or cost < best_cost:
                best_goal = coord
                best_state = (coord, current_phase)
                best_cost = cost

        if current_phase == "platform":
            for edge in domain.lift_edges:
                if edge.platform_coord != coord:
                    continue
                next_state = (edge.lift_coord, "trunk")
                if next_state in visited:
                    continue
                visited.add(next_state)
                parent[next_state] = (coord, current_phase)
                queue.append((edge.lift_coord, "trunk", cost + 1))
            continue

        for neighbor in neighbors4(coord):
            if neighbor in domain.blocked_cells:
                continue
            if neighbor not in domain.traversable_cells and neighbor not in goals:
                continue
            next_state = (neighbor, "trunk")
            if next_state in visited:
                continue
            visited.add(next_state)
            parent[next_state] = (coord, current_phase)
            queue.append((neighbor, "trunk", cost + 1))

    if best_goal is None or best_state is None:
        return RouteProbeResult(
            reachable=False,
            cost=0,
            reached_goal=None,
            path=(),
            expanded_nodes=expanded,
        )

    path_rev: list[Coord] = []
    state: tuple[Coord, str] | None = best_state
    while state is not None:
        path_rev.append(state[0])
        state = parent.get(state)
    return RouteProbeResult(
        reachable=True,
        cost=best_cost,
        reached_goal=best_goal,
        path=tuple(reversed(path_rev)),
        expanded_nodes=expanded,
    )


__all__ = ["RouteProbeResult", "initial_phase", "probe_route"]
