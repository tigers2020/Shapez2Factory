"""Phase G — bounded route feasibility probe from route_probe_start (PR2)."""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord, neighbors4_server
from django_apps.asteroid_lab.optimization.enums import (
    RouteProbeFailureReason,
    TransportKind,
    TransportMask,
)
from django_apps.asteroid_lab.optimization.gene_projection import ProjectedGenePlacement
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RouteGoal,
    TopologyGraph,
)
from django_apps.asteroid_lab.optimization.route_domain import (
    RouteCellDomain,
    RouteDomainSnapshotBuilder,
)


@dataclass(frozen=True, slots=True)
class RouteProbeInput:
    start: Coord
    goals: frozenset[RouteGoal]
    route_domain: dict[Coord, RouteCellDomain]
    topology_graph: TopologyGraph
    max_expansions: int
    transport_kind: TransportKind
    goal_priority_weight: int = 10


@dataclass(frozen=True, slots=True)
class RouteProbeResult:
    reachable: bool
    path: tuple[Coord, ...]
    cost: int
    expanded_nodes: int
    reached_goal: RouteGoal | None
    goal_priority: int | None
    failure_reason: RouteProbeFailureReason | None


def build_route_domain_for_projected_gene_probe(
    inp: OptimizationInput,
    projected: ProjectedGenePlacement,
) -> dict[Coord, RouteCellDomain]:
    """Candidate-phase provisional occupancy only. This does not commit placement."""

    provisional = projected.occupied_cells | frozenset({projected.fixed_output_transport})
    return RouteDomainSnapshotBuilder.build_snapshot(
        inp,
        provisional_blocked_cells=provisional,
    )


def _mask_allows(kind: TransportKind, mask: TransportMask) -> bool:
    if kind == TransportKind.SHAPE_BELT:
        return bool(mask & TransportMask.SHAPE_BELT)
    if kind == TransportKind.FLUID_PIPE:
        return bool(mask & TransportMask.FLUID_PIPE)
    return mask == TransportMask.NONE


def _goal_cells(goals: frozenset[RouteGoal], transport_kind: TransportKind) -> frozenset[Coord]:
    out: set[Coord] = set()
    for g in goals:
        if g.transport_kind is not None and g.transport_kind != transport_kind:
            continue
        out.add(g.coord)
    return frozenset(out)


def _selection_score(path_cost: int, goal: RouteGoal, weight: int) -> tuple[int, int, Coord, str]:
    return (path_cost + weight * goal.priority, goal.priority, goal.coord, goal.goal_kind.value)


def _domain_uses_uniform_unit_cost(domain: dict[Coord, RouteCellDomain]) -> bool:
    return all(cell.traversal_cost == 1 for cell in domain.values())


def _probe_early_exit(probe: RouteProbeInput) -> RouteProbeResult | None:
    domain = probe.route_domain
    start = probe.start
    if start not in domain:
        return RouteProbeResult(
            reachable=False,
            path=(),
            cost=0,
            expanded_nodes=0,
            reached_goal=None,
            goal_priority=None,
            failure_reason=RouteProbeFailureReason.INVALID_ROUTE_DOMAIN,
        )

    if domain[start].hard_blocked:
        return RouteProbeResult(
            reachable=False,
            path=(),
            cost=0,
            expanded_nodes=0,
            reached_goal=None,
            goal_priority=None,
            failure_reason=RouteProbeFailureReason.START_BLOCKED,
        )

    if not _goal_cells(probe.goals, probe.transport_kind):
        return RouteProbeResult(
            reachable=False,
            path=(),
            cost=0,
            expanded_nodes=0,
            reached_goal=None,
            goal_priority=None,
            failure_reason=RouteProbeFailureReason.NO_GOAL_CELLS,
        )
    return None


def _finalize_unreachable(*, expanded: int, max_expansions: int) -> RouteProbeResult:
    reason = (
        RouteProbeFailureReason.BUDGET_EXCEEDED
        if expanded >= max_expansions
        else RouteProbeFailureReason.EXHAUSTED
    )
    return RouteProbeResult(
        reachable=False,
        path=(),
        cost=0,
        expanded_nodes=expanded,
        reached_goal=None,
        goal_priority=None,
        failure_reason=reason,
    )


def _build_success_result(
    *,
    best_goal: RouteGoal,
    best_path_cost: int,
    parent: dict[Coord, Coord | None],
    expanded: int,
) -> RouteProbeResult:
    path_rev: list[Coord] = []
    cur: Coord | None = best_goal.coord
    while cur is not None:
        path_rev.append(cur)
        cur = parent.get(cur)
    path = tuple(reversed(path_rev))
    return RouteProbeResult(
        reachable=True,
        path=path,
        cost=best_path_cost,
        expanded_nodes=expanded,
        reached_goal=best_goal,
        goal_priority=best_goal.priority,
        failure_reason=None,
    )


def _run_bounded_uniform_cost(probe: RouteProbeInput) -> RouteProbeResult:
    early = _probe_early_exit(probe)
    if early is not None:
        return early

    domain = probe.route_domain
    start = probe.start
    goal_cells = _goal_cells(probe.goals, probe.transport_kind)
    goals_by_coord: dict[Coord, RouteGoal] = {}
    for g in probe.goals:
        if g.coord in goal_cells:
            goals_by_coord[g.coord] = g

    frontier: list[tuple[int, Coord]] = [(0, start)]
    heapq.heapify(frontier)
    best_cost: dict[Coord, int] = {start: 0}
    parent: dict[Coord, Coord | None] = {start: None}
    expanded = 0

    best_goal: RouteGoal | None = None
    best_path_cost = 0
    best_score: tuple[int, int, Coord, str] | None = None

    while frontier and expanded < probe.max_expansions:
        cost, current = heapq.heappop(frontier)
        if cost != best_cost.get(current, cost + 1):
            continue
        expanded += 1

        if current in goal_cells:
            g = goals_by_coord[current]
            score = _selection_score(cost, g, probe.goal_priority_weight)
            if best_score is None or score < best_score:
                best_score = score
                best_goal = g
                best_path_cost = cost

        for nb in neighbors4_server(current):
            if nb not in domain:
                continue
            cell = domain[nb]
            if cell.hard_blocked:
                continue
            if not _mask_allows(probe.transport_kind, cell.transport_mask):
                continue
            new_cost = cost + cell.traversal_cost
            if nb in best_cost and best_cost[nb] <= new_cost:
                continue
            best_cost[nb] = new_cost
            parent[nb] = current
            heapq.heappush(frontier, (new_cost, nb))

    if best_goal is None:
        return _finalize_unreachable(expanded=expanded, max_expansions=probe.max_expansions)
    return _build_success_result(
        best_goal=best_goal,
        best_path_cost=best_path_cost,
        parent=parent,
        expanded=expanded,
    )


def _run_bounded_bfs(probe: RouteProbeInput) -> RouteProbeResult:
    early = _probe_early_exit(probe)
    if early is not None:
        return early

    domain = probe.route_domain
    start = probe.start
    goal_cells = _goal_cells(probe.goals, probe.transport_kind)
    goals_by_coord: dict[Coord, RouteGoal] = {}
    for g in probe.goals:
        if g.coord in goal_cells:
            goals_by_coord[g.coord] = g

    frontier: deque[Coord] = deque([start])
    best_cost: dict[Coord, int] = {start: 0}
    parent: dict[Coord, Coord | None] = {start: None}
    expanded = 0

    best_goal: RouteGoal | None = None
    best_path_cost = 0
    best_score: tuple[int, int, Coord, str] | None = None

    while frontier and expanded < probe.max_expansions:
        current = frontier.popleft()
        cost = best_cost[current]
        expanded += 1

        if current in goal_cells:
            g = goals_by_coord[current]
            score = _selection_score(cost, g, probe.goal_priority_weight)
            if best_score is None or score < best_score:
                best_score = score
                best_goal = g
                best_path_cost = cost

        for nb in neighbors4_server(current):
            if nb not in domain:
                continue
            cell = domain[nb]
            if cell.hard_blocked:
                continue
            if not _mask_allows(probe.transport_kind, cell.transport_mask):
                continue
            new_cost = cost + 1
            if nb in best_cost and best_cost[nb] <= new_cost:
                continue
            best_cost[nb] = new_cost
            parent[nb] = current
            frontier.append(nb)

    if best_goal is None:
        return _finalize_unreachable(expanded=expanded, max_expansions=probe.max_expansions)
    return _build_success_result(
        best_goal=best_goal,
        best_path_cost=best_path_cost,
        parent=parent,
        expanded=expanded,
    )


def run_route_probe(probe: RouteProbeInput) -> RouteProbeResult:
    """Bounded feasibility search from ``route_probe_start``; does not materialize transport."""

    if _domain_uses_uniform_unit_cost(probe.route_domain):
        return _run_bounded_bfs(probe)
    return _run_bounded_uniform_cost(probe)


def run_route_probe_uniform_cost(probe: RouteProbeInput) -> RouteProbeResult:
    """Force heap-based uniform-cost search (tests / parity)."""

    return _run_bounded_uniform_cost(probe)
