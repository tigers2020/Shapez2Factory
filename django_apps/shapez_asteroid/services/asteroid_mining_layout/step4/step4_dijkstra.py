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
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_permission import (  # noqa: E501
    step4_is_routing_goal,
    step4_step_cost,
)

_MAX_STEP4_DIJKSTRA_POPS = 250_000


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
    cheap_reuse_cells: frozenset[Coord] | None = None,
    search_stats: dict[str, Any] | None = None,
    max_heap_pops: int | None = None,
) -> tuple[Coord, ...] | None:
    """Shortest path (positive costs) from ``stub_cell``; path[0] == stub_cell.

    When ``goal_cells`` is set, termination is ``u in goal_cells`` (still §9.2 trunk/external).
    Otherwise the legacy ``step4_is_routing_goal`` predicate is used.

    If ``search_stats`` is a dict, it is filled on exit: ``expanded_nodes`` (visited count),
    ``heap_pops``, ``stop_reason`` in ``success`` | ``exhausted`` | ``budget``.

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

    if search_stats is not None:
        _s4sd.fill_goal_geometry_search_stats(stub_cell, goal_cells, search_stats)

    def _stamp_time() -> None:
        if search_stats is not None:
            search_stats["search_time_ms"] = (time.perf_counter() - t0) * 1000.0

    while heap:
        max_frontier_size = max(max_frontier_size, len(heap))
        pops += 1
        if pops > pop_cap:
            if search_stats is not None:
                search_stats["expanded_nodes"] = len(visited)
                search_stats["heap_pops"] = pops
                search_stats["stop_reason"] = "budget"
                search_stats["max_frontier_size"] = max_frontier_size
                search_stats["frontier_stop_reason"] = search_stats["stop_reason"]
                _stamp_time()
            return None
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        if d > dist.get(u, float("inf")):
            continue
        visited.add(u)
        if goal_cells is not None:
            legacy_goal = step4_is_routing_goal(
                u, want_role=want_role, trunk=trunk, is_external=is_external
            )
            reached = u != stub_cell and (u in goal_cells or legacy_goal)
        else:
            reached = step4_is_routing_goal(
                u, want_role=want_role, trunk=trunk, is_external=is_external
            )
        if reached:
            chain: list[Coord] = []
            cur: Coord | None = u
            while cur is not None:
                chain.append(cur)
                cur = prev[cur]
            chain.reverse()
            if search_stats is not None:
                search_stats["expanded_nodes"] = len(visited)
                search_stats["heap_pops"] = pops
                search_stats["stop_reason"] = "success"
                search_stats["max_frontier_size"] = max_frontier_size
                search_stats["frontier_stop_reason"] = search_stats["stop_reason"]
                _stamp_time()
            return tuple(chain)

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
    if search_stats is not None:
        search_stats["expanded_nodes"] = len(visited)
        search_stats["heap_pops"] = pops
        search_stats["stop_reason"] = "exhausted"
        search_stats["max_frontier_size"] = max_frontier_size
        search_stats["frontier_stop_reason"] = search_stats["stop_reason"]
        _stamp_time()
    return None
