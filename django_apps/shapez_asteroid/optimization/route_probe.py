"""Bounded uniform-cost route feasibility probe (Sequence 3 / Phase 4)."""

from __future__ import annotations

import heapq
import time
from collections import defaultdict
from collections.abc import Mapping

from django_apps.shapez_asteroid.optimization.coords import Coord, neighbors4_server
from django_apps.shapez_asteroid.optimization.dto import (
    RouteCellDomain,
    RouteGoal,
    RouteProbeInput,
    RouteProbeResult,
    TopologyGraph,
)
from django_apps.shapez_asteroid.optimization.enums import (
    RouteGoalKind,
    RouteProbeFailureReason,
    TransportKind,
    TransportMask,
)


def _goal_kind_rank(k: RouteGoalKind) -> int:
    return tuple(RouteGoalKind).index(k)


def _mask_allows(mask: TransportMask, kind: TransportKind) -> bool:
    if kind is TransportKind.SHAPE_BELT:
        return bool(mask & TransportMask.SHAPE_BELT)
    if kind is TransportKind.FLUID_PIPE:
        return bool(mask & TransportMask.FLUID_PIPE)
    return False


def _build_adjacency(g: TopologyGraph) -> dict[Coord, tuple[Coord, ...]]:
    adj: dict[Coord, set[Coord]] = defaultdict(set)
    for e in g.edges:
        adj[e.a].add(e.b)
        adj[e.b].add(e.a)
    return {c: tuple(sorted(ns, key=lambda z: (z.x, z.y))) for c, ns in adj.items()}


def _edge_cost(u: Coord, v: Coord, g: TopologyGraph) -> int | None:
    """Return edge traversal cost if a topology edge exists, else ``None``."""

    a, b = (u, v) if (u.x, u.y) <= (v.x, v.y) else (v, u)
    for e in g.edges:
        if e.a == a and e.b == b:
            return e.traversal_cost
    return None


def _neighbor_coords(u: Coord, topo: TopologyGraph, *, use_graph: bool) -> tuple[Coord, ...]:
    if use_graph:
        adj = _build_adjacency(topo)
        return adj.get(u, ())
    return neighbors4_server(u)


def _merge_route_domain(
    base: Mapping[Coord, RouteCellDomain],
    occupied_overlay: frozenset[Coord],
) -> tuple[dict[Coord, RouteCellDomain], frozenset[Coord]]:
    """Copy domain; overlay coords become ``hard_blocked`` (returns merged map + overlay)."""

    out = dict(base)
    overlay: set[Coord] = set()
    for c in sorted(occupied_overlay, key=lambda z: (z.x, z.y)):
        cell = base.get(c)
        if cell is None:
            continue
        if cell.hard_blocked:
            continue
        overlay.add(c)
        out[c] = RouteCellDomain(
            coord=c,
            route_class=cell.route_class,
            traversal_cost=cell.traversal_cost,
            hard_blocked=True,
            carve_allowed=cell.carve_allowed,
            transport_mask=TransportMask.NONE,
        )
    return out, frozenset(overlay)


def _goal_matches_transport(g: RouteGoal, tk: TransportKind) -> bool:
    if g.transport_kind is None:
        return True
    return g.transport_kind is tk


def _filter_goals(
    goals: frozenset[RouteGoal],
    *,
    domain: Mapping[Coord, RouteCellDomain],
    tk: TransportKind,
) -> tuple[RouteGoal, ...]:
    kept: list[RouteGoal] = []
    for g in sorted(goals, key=lambda z: (z.coord.x, z.coord.y, z.goal_kind.value, z.priority)):
        if g.coord not in domain:
            continue
        if not _goal_matches_transport(g, tk):
            continue
        kept.append(g)
    return tuple(kept)


def _better_selection(
    a: tuple[int, int, RouteGoal],
    b: tuple[int, int, RouteGoal],
) -> bool:
    """``a`` wins if it has lower route_selection_score, then tie-break."""

    score_a, path_a, ga = a
    score_b, path_b, gb = b
    if score_a != score_b:
        return score_a < score_b
    if path_a != path_b:
        return path_a < path_b
    if ga.priority != gb.priority:
        return ga.priority < gb.priority
    if (ga.coord.x, ga.coord.y) != (gb.coord.x, gb.coord.y):
        return (ga.coord.x, ga.coord.y) < (gb.coord.x, gb.coord.y)
    return _goal_kind_rank(ga.goal_kind) < _goal_kind_rank(gb.goal_kind)


def run_route_probe(
    inp: RouteProbeInput,
    *,
    occupied_cells: frozenset[Coord] | None = None,
) -> RouteProbeResult:
    """Feasibility-only UCS; does not mutate ``inp.route_domain``."""

    overlay = occupied_cells or frozenset()
    domain_map, overlay_blocked = _merge_route_domain(inp.route_domain, overlay)

    if inp.transport_kind not in (TransportKind.SHAPE_BELT, TransportKind.FLUID_PIPE):
        return RouteProbeResult(
            reachable=False,
            path=(),
            cost=0,
            expanded_nodes=0,
            reached_goal=None,
            goal_priority=None,
            failure_reason=RouteProbeFailureReason.INVALID_TRANSPORT_KIND,
        )

    tk = inp.transport_kind
    start = inp.start
    if start not in inp.route_domain:
        return RouteProbeResult(
            reachable=False,
            path=(),
            cost=0,
            expanded_nodes=0,
            reached_goal=None,
            goal_priority=None,
            failure_reason=RouteProbeFailureReason.INVALID_ROUTE_DOMAIN,
        )

    merged_start = domain_map[start]

    if merged_start.hard_blocked:
        if start in overlay_blocked:
            return RouteProbeResult(
                reachable=False,
                path=(),
                cost=0,
                expanded_nodes=0,
                reached_goal=None,
                goal_priority=None,
                failure_reason=RouteProbeFailureReason.BLOCKED_BY_OCCUPIED,
            )
        return RouteProbeResult(
            reachable=False,
            path=(),
            cost=0,
            expanded_nodes=0,
            reached_goal=None,
            goal_priority=None,
            failure_reason=RouteProbeFailureReason.START_BLOCKED,
        )

    if not _mask_allows(merged_start.transport_mask, tk):
        return RouteProbeResult(
            reachable=False,
            path=(),
            cost=0,
            expanded_nodes=0,
            reached_goal=None,
            goal_priority=None,
            failure_reason=RouteProbeFailureReason.START_BLOCKED,
        )

    goals = _filter_goals(inp.goals, domain=inp.route_domain, tk=tk)
    if not goals:
        return RouteProbeResult(
            reachable=False,
            path=(),
            cost=0,
            expanded_nodes=0,
            reached_goal=None,
            goal_priority=None,
            failure_reason=RouteProbeFailureReason.NO_GOAL_CELLS,
        )

    goal_at: dict[Coord, tuple[RouteGoal, ...]] = defaultdict(tuple)
    for g in goals:
        goal_at[g.coord] = goal_at[g.coord] + (g,)

    use_graph = bool(inp.topology_graph.edges)

    def neighbors(u: Coord) -> tuple[Coord, ...]:
        return _neighbor_coords(u, inp.topology_graph, use_graph=use_graph)

    def traversable_cell(c: RouteCellDomain) -> bool:
        if c.hard_blocked:
            return False
        return _mask_allows(c.transport_mask, tk)

    dom_neighbors = [v for v in neighbors(start) if v in domain_map]
    expandable = [v for v in dom_neighbors if traversable_cell(domain_map[v])]

    if not expandable and start not in goal_at:
        if dom_neighbors and all(
            domain_map[v].hard_blocked and v in overlay_blocked for v in dom_neighbors
        ):
            return RouteProbeResult(
                reachable=False,
                path=(),
                cost=0,
                expanded_nodes=0,
                reached_goal=None,
                goal_priority=None,
                failure_reason=RouteProbeFailureReason.BLOCKED_BY_OCCUPIED,
            )

    w = inp.goal_priority_weight

    if start in goal_at:
        best: tuple[int, int, RouteGoal] | None = None
        for g in goal_at[start]:
            if not _goal_matches_transport(g, tk):
                continue
            path_cost = 0
            score = path_cost + w * g.priority
            cand = (score, path_cost, g)
            if best is None or _better_selection(cand, best):
                best = cand
        if best is not None:
            _, pc, gg = best
            return RouteProbeResult(
                reachable=True,
                path=(start,),
                cost=pc,
                expanded_nodes=0,
                reached_goal=gg,
                goal_priority=gg.priority,
                failure_reason=None,
            )

    INF = 10**18
    dist: dict[Coord, int] = {start: 0}
    parent: dict[Coord, Coord | None] = {start: None}
    heap: list[tuple[int, int, Coord]] = []
    seq = 0
    heapq.heappush(heap, (0, seq, start))
    seq += 1

    expanded_nodes = 0
    best_goal_bundle: tuple[int, int, RouteGoal] | None = None

    while heap:
        cost_u, _, u = heapq.heappop(heap)
        if cost_u != dist.get(u, INF):
            continue

        expanded_nodes += 1

        if (
            inp.wall_clock_deadline_perf is not None
            and time.perf_counter() >= inp.wall_clock_deadline_perf
        ):
            return RouteProbeResult(
                reachable=False,
                path=(),
                cost=0,
                expanded_nodes=expanded_nodes,
                reached_goal=None,
                goal_priority=None,
                failure_reason=RouteProbeFailureReason.WALL_CLOCK_ABORT,
            )

        if u in goal_at:
            for g in goal_at[u]:
                if not _goal_matches_transport(g, tk):
                    continue
                path_cost = cost_u
                score = path_cost + w * g.priority
                cand = (score, path_cost, g)
                if best_goal_bundle is None or _better_selection(cand, best_goal_bundle):
                    best_goal_bundle = cand

        if expanded_nodes > inp.max_expansions:
            if best_goal_bundle is None:
                return RouteProbeResult(
                    reachable=False,
                    path=(),
                    cost=0,
                    expanded_nodes=expanded_nodes,
                    reached_goal=None,
                    goal_priority=None,
                    failure_reason=RouteProbeFailureReason.BUDGET_EXCEEDED,
                )
            break

        for v in neighbors(u):
            if v not in domain_map:
                continue
            cv = domain_map[v]
            if not traversable_cell(cv):
                continue
            edge_extra = _edge_cost(u, v, inp.topology_graph) if use_graph else None
            if use_graph and edge_extra is None:
                continue
            step_edge = 1 if edge_extra is None else edge_extra
            alt = cost_u + step_edge + cv.traversal_cost
            if alt < dist.get(v, INF):
                dist[v] = alt
                parent[v] = u
                heapq.heappush(heap, (alt, seq, v))
                seq += 1

    if best_goal_bundle is None:
        if dom_neighbors and all(
            domain_map[v].hard_blocked and v in overlay_blocked for v in dom_neighbors
        ):
            fr = RouteProbeFailureReason.BLOCKED_BY_OCCUPIED
        else:
            fr = RouteProbeFailureReason.EXHAUSTED
        return RouteProbeResult(
            reachable=False,
            path=(),
            cost=0,
            expanded_nodes=expanded_nodes,
            reached_goal=None,
            goal_priority=None,
            failure_reason=fr,
        )

    _, best_cost, best_goal = best_goal_bundle
    cur = best_goal.coord
    chain: list[Coord] = []
    while True:
        chain.append(cur)
        p = parent[cur]
        if p is None:
            break
        cur = p
    path = tuple(reversed(chain))

    return RouteProbeResult(
        reachable=True,
        path=path,
        cost=best_cost,
        expanded_nodes=expanded_nodes,
        reached_goal=best_goal,
        goal_priority=best_goal.priority,
        failure_reason=None,
    )
