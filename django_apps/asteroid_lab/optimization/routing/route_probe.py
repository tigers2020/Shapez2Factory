"""Bounded route feasibility probe on skeleton-aware route domain (PR-3 + EVTC-7)."""

from __future__ import annotations

import heapq
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


def _step_cost_lookup(domain: RouteCellDomain) -> dict[Coord, int]:
    return dict(domain.step_costs)


def _goal_is_better(
    *,
    goal: Coord,
    cost: int,
    best_goal: Coord | None,
    best_cost: int,
    goal_priority: dict[Coord, int],
) -> bool:
    if best_goal is None:
        return True
    if cost < best_cost:
        return True
    if cost > best_cost:
        return False
    new_priority = goal_priority.get(goal, 0)
    old_priority = goal_priority.get(best_goal, 0)
    if new_priority != old_priority:
        return new_priority > old_priority
    return goal < best_goal


def _reconstruct_path(
    parent: dict[tuple[Coord, str], tuple[Coord, str] | None],
    end_state: tuple[Coord, str],
) -> tuple[Coord, ...]:
    path_rev: list[Coord] = []
    state: tuple[Coord, str] | None = end_state
    while state is not None:
        path_rev.append(state[0])
        state = parent.get(state)
    return tuple(reversed(path_rev))


def _probe_route_unweighted(
    domain: RouteCellDomain,
    start: Coord,
    goals: frozenset[Coord],
    *,
    max_expansions: int,
    goal_priority: dict[Coord, int],
) -> RouteProbeResult:
    phase = initial_phase(domain, start)
    if phase is None:
        return RouteProbeResult(False, 0, None, (), 0)
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
            if _goal_is_better(
                goal=coord,
                cost=cost,
                best_goal=best_goal,
                best_cost=best_cost,
                goal_priority=goal_priority,
            ):
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
        return RouteProbeResult(False, 0, None, (), expanded)
    return RouteProbeResult(
        True,
        best_cost,
        best_goal,
        _reconstruct_path(parent, best_state),
        expanded,
    )


def _probe_route_weighted(
    domain: RouteCellDomain,
    start: Coord,
    goals: frozenset[Coord],
    *,
    max_expansions: int,
    goal_priority: dict[Coord, int],
    step_costs: dict[Coord, int],
) -> RouteProbeResult:
    phase = initial_phase(domain, start)
    if phase is None or start in domain.blocked_cells:
        return RouteProbeResult(False, 0, None, (), 0)

    heap: list[tuple[int, int, Coord, str]] = [(0, 0, start, phase)]
    visited: dict[tuple[Coord, str], int] = {(start, phase): 0}
    parent: dict[tuple[Coord, str], tuple[Coord, str] | None] = {(start, phase): None}
    expanded = 0
    tie_counter = 0
    best_goal: Coord | None = None
    best_cost = 0

    while heap and expanded < max_expansions:
        cost, _tie, coord, current_phase = heapq.heappop(heap)
        expanded += 1
        state = (coord, current_phase)
        if visited.get(state, 10**9) < cost:
            continue

        if current_phase == "trunk" and coord in goals:
            if _goal_is_better(
                goal=coord,
                cost=cost,
                best_goal=best_goal,
                best_cost=best_cost,
                goal_priority=goal_priority,
            ):
                best_goal = coord
                best_cost = cost

        if current_phase == "platform":
            for edge in domain.lift_edges:
                if edge.platform_coord != coord:
                    continue
                next_state = (edge.lift_coord, "trunk")
                next_cost = cost + step_costs.get(edge.lift_coord, 2)
                if visited.get(next_state, 10**9) <= next_cost:
                    continue
                visited[next_state] = next_cost
                parent[next_state] = state
                tie_counter += 1
                heapq.heappush(heap, (next_cost, tie_counter, edge.lift_coord, "trunk"))
            continue

        for neighbor in neighbors4(coord):
            if neighbor in domain.blocked_cells:
                continue
            if neighbor not in domain.traversable_cells and neighbor not in goals:
                continue
            next_state = (neighbor, "trunk")
            next_cost = cost + step_costs.get(neighbor, 5)
            if visited.get(next_state, 10**9) <= next_cost:
                continue
            visited[next_state] = next_cost
            parent[next_state] = state
            tie_counter += 1
            heapq.heappush(heap, (next_cost, tie_counter, neighbor, "trunk"))

    if best_goal is None:
        return RouteProbeResult(False, 0, None, (), expanded)
    end_state = (best_goal, "trunk")
    return RouteProbeResult(
        True,
        best_cost,
        best_goal,
        _reconstruct_path(parent, end_state),
        expanded,
    )


def _effective_probe_goals(start: Coord, goals: frozenset[Coord]) -> frozenset[Coord]:
    """Drop ``start`` from goals when other targets exist (avoid zero-hop false success)."""

    if start not in goals:
        return goals
    remaining = frozenset(goal for goal in goals if goal != start)
    return remaining if remaining else goals


def probe_route(
    domain: RouteCellDomain,
    start: Coord,
    goals: frozenset[Coord],
    *,
    max_expansions: int = 500,
    goal_priority: dict[Coord, int] | None = None,
) -> RouteProbeResult:
    """BFS or weighted shortest path from ``start`` to connector goals."""

    priorities = goal_priority or {}
    if not goals:
        return RouteProbeResult(False, 0, None, (), 0)
    goals = _effective_probe_goals(start, goals)
    if goals == frozenset({start}):
        return RouteProbeResult(True, 0, start, (start,), 0)

    step_costs = _step_cost_lookup(domain)
    if step_costs:
        return _probe_route_weighted(
            domain,
            start,
            goals,
            max_expansions=max_expansions,
            goal_priority=priorities,
            step_costs=step_costs,
        )
    return _probe_route_unweighted(
        domain,
        start,
        goals,
        max_expansions=max_expansions,
        goal_priority=priorities,
    )


__all__ = ["RouteProbeResult", "initial_phase", "probe_route"]
