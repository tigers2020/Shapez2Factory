"""STEP4 merge-aware stub→trunk routing: bounded Dijkstra."""

from __future__ import annotations

import heapq
import time
from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_search_diagnostics as _s4sd,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_models import (
    Step4RoutingContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_permission import (  # noqa: E501
    step4_is_routing_goal,
    step4_step_cost,
)

_MAX_STEP4_DIJKSTRA_POPS = 250_000

# Telemetry-only: goals among cells popped into ``visited`` (same predicate as goal termination).
DIJKSTRA_REACHABLE_GOAL_COUNT_KEY = "dijkstra_reachable_goal_count"
DIJKSTRA_REACHABLE_TRUNK_GOAL_COUNT_KEY = "dijkstra_reachable_trunk_goal_count"
DIJKSTRA_REACHABLE_MARGIN_GOAL_COUNT_KEY = "dijkstra_reachable_margin_goal_count"


def dijkstra_route_step4(
    stub_cell: Coord,
    *,
    want_role: str,
    cells: dict[Coord, dict[str, Any]],
    blocked: frozenset[Coord],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    trunk: frozenset[Coord],
    goal_cells: frozenset[Coord] | None = None,
    margin_cells: frozenset[Coord] | None = None,
    cheap_reuse_cells: frozenset[Coord] | None = None,
    search_stats: dict[str, Any] | None = None,
    max_heap_pops: int | None = None,
) -> tuple[Coord, ...] | None:
    """Shortest path (positive costs) from ``stub_cell``; path[0] == stub_cell.

    When ``goal_cells`` is set, termination is ``u in goal_cells`` (still §9.2 trunk/external).
    Otherwise the legacy ``step4_is_routing_goal`` predicate is used.

    If ``search_stats`` is a dict, it is filled on exit: ``expanded_nodes`` (visited count),
    ``heap_pops``, ``stop_reason`` in ``success`` | ``exhausted`` | ``budget``,
    and ``dijkstra_reachable_goal_count`` / ``dijkstra_reachable_trunk_goal_count`` /
    ``dijkstra_reachable_margin_goal_count`` (goals among popped ``visited``; telemetry only).

    ``margin_cells``: optional frozenset for margin-goal split in reachable counts; omit when
    unknown (margin count stays 0).

    ``max_heap_pops``: optional heap pop cap (defaults to ``_MAX_STEP4_DIJKSTRA_POPS``).
    """

    t0 = time.perf_counter()
    pop_cap = _MAX_STEP4_DIJKSTRA_POPS if max_heap_pops is None else int(max_heap_pops)
    dist: dict[Coord, float] = {stub_cell: 0.0}
    prev: dict[Coord, Coord | None] = {stub_cell: None}
    heap: list[tuple[float, Coord]] = [(0.0, stub_cell)]
    visited: set[Coord] = set()
    pops = 0
    max_frontier_size = 0
    rg = rt = rm = 0
    stop_reason: str | None = None
    result: tuple[Coord, ...] | None = None

    if search_stats is not None:
        _s4sd.fill_goal_geometry_search_stats(stub_cell, goal_cells, search_stats)

    while heap:
        pops += 1
        if pops > pop_cap:
            max_frontier_size = max(max_frontier_size, len(heap))
            stop_reason = "budget"
            break
        d, u = heapq.heappop(heap)
        max_frontier_size = max(max_frontier_size, len(heap))
        if u in visited:
            continue
        if d > dist.get(u, float("inf")):
            continue
        visited.add(u)

        if goal_cells is not None:
            if u in goal_cells:
                reached = u != stub_cell
                if search_stats is not None and u != stub_cell:
                    rg += 1
                    if u in trunk:
                        rt += 1
                    if margin_cells is not None and u in margin_cells:
                        rm += 1
            else:
                legacy_goal = step4_is_routing_goal(
                    u, want_role=want_role, trunk=trunk, is_external=is_external
                )
                reached = u != stub_cell and legacy_goal
                if search_stats is not None and u != stub_cell and legacy_goal:
                    rg += 1
                    if u in trunk:
                        rt += 1
                    if margin_cells is not None and u in margin_cells:
                        rm += 1
        else:
            reached = step4_is_routing_goal(
                u, want_role=want_role, trunk=trunk, is_external=is_external
            )
            if search_stats is not None and u != stub_cell and reached:
                rg += 1
                if u in trunk:
                    rt += 1
                if margin_cells is not None and u in margin_cells:
                    rm += 1

        if reached:
            chain: list[Coord] = []
            cur: Coord | None = u
            while cur is not None:
                chain.append(cur)
                cur = prev[cur]
            chain.reverse()
            result = tuple(chain)
            stop_reason = "success"
            break

        x, y = u
        for v in neighbors4(x, y):
            if v in blocked and v != stub_cell:
                continue
            step = step4_step_cost(
                v,
                want_role=want_role,
                cells=cells,
                mineable=mineable,
                asteroid=asteroid,
                is_external=is_external,
                cheap_reuse_cells=cheap_reuse_cells,
            )
            if step is None:
                continue
            nd = d + step
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
        max_frontier_size = max(max_frontier_size, len(heap))

    if stop_reason is None:
        stop_reason = "exhausted"

    if search_stats is not None:
        search_stats[DIJKSTRA_REACHABLE_GOAL_COUNT_KEY] = rg
        search_stats[DIJKSTRA_REACHABLE_TRUNK_GOAL_COUNT_KEY] = rt
        search_stats[DIJKSTRA_REACHABLE_MARGIN_GOAL_COUNT_KEY] = rm
        search_stats["expanded_nodes"] = len(visited)
        search_stats["heap_pops"] = pops
        search_stats["stop_reason"] = stop_reason
        search_stats["max_frontier_size"] = max_frontier_size
        search_stats["frontier_stop_reason"] = stop_reason
        search_stats["search_time_ms"] = (time.perf_counter() - t0) * 1000.0

    return result


def dijkstra_route_step4_ctx(
    ctx: Step4RoutingContext,
    cells: dict[Coord, dict[str, Any]],
    stub_cell: Coord,
    *,
    want_role: str,
    blocked: frozenset[Coord],
    trunk: frozenset[Coord],
    goal_cells: frozenset[Coord] | None = None,
    margin_cells: frozenset[Coord] | None = None,
    cheap_reuse_cells: frozenset[Coord] | None = None,
    search_stats: dict[str, Any] | None = None,
    max_heap_pops: int | None = None,
) -> tuple[Coord, ...] | None:
    """Same as :func:`dijkstra_route_step4` with grid constants taken from ``ctx``."""

    return dijkstra_route_step4(
        stub_cell,
        want_role=want_role,
        cells=cells,
        blocked=blocked,
        mineable=ctx.mineable,
        asteroid=ctx.asteroid,
        is_external=ctx.is_external,
        trunk=trunk,
        goal_cells=goal_cells,
        margin_cells=margin_cells,
        cheap_reuse_cells=cheap_reuse_cells,
        search_stats=search_stats,
        max_heap_pops=max_heap_pops,
    )
