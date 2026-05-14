"""Weighted grid search for demolition / repair scenarios."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    INF_COST,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


@dataclass(frozen=True)
class DemolitionPathResult:
    """find_min_demolition_path 결과 DTO.

        repair/demolition 경로와 총 비용을 함께 보존한다 (§3.5 route/cost grid).

    상세: documents/Algorithm/mining_solver_cursor_sessions/01_project_overview.md"""

    path: tuple[Coord, ...]
    total_cost: int


def find_min_demolition_path(
    start: Coord,
    goals: set[Coord],
    *,
    asteroid_cells: set[Coord],
    buildings: dict[Coord, str],
    transport_cells: frozenset[Coord],
    locked_cells: frozenset[Coord],
    search_margin: int,
    allow_mineable_route: bool = False,
    mineable_route_step_cost: int | None = None,
) -> DemolitionPathResult | None:
    """Shortest-path minimal demolition cost on cardinal grid (Shapez no-x0 rules)."""

    _ = buildings

    bbox_pts = [start, *goals]
    x_lo = min(p[0] for p in bbox_pts) - search_margin
    x_hi = max(p[0] for p in bbox_pts) + search_margin
    y_lo = min(p[1] for p in bbox_pts) - search_margin
    y_hi = max(p[1] for p in bbox_pts) + search_margin

    def in_search_bbox(cell: Coord) -> bool:
        """repair 탐색을 goal 주변 bbox로 제한한다 (§3.5 route/cost grid)."""
        x, y = cell
        return x_lo <= x <= x_hi and y_lo <= y <= y_hi

    def enter_cost(cell: Coord) -> int:
        """한 칸 진입 demolition/repair cost를 계산한다 (§3.5 route/cost grid)."""
        if cell in goals:
            return 0
        if cell in locked_cells:
            return INF_COST
        if not in_search_bbox(cell):
            return INF_COST
        if cell in asteroid_cells:
            if allow_mineable_route:
                return (
                    mineable_route_step_cost if mineable_route_step_cost is not None else INF_COST
                )
            return INF_COST
        return 1

    pq: list[tuple[int, Coord]] = [(0, start)]
    best: dict[Coord, int] = {start: 0}
    parent: dict[Coord, Coord | None] = {start: None}

    while pq:
        cost, cur = heapq.heappop(pq)
        if cost != best.get(cur, INF_COST):
            continue
        if cur in goals:
            path: list[Coord] = []
            walk: Coord | None = cur
            while walk is not None:
                path.append(walk)
                walk = parent.get(walk)
            path.reverse()
            return DemolitionPathResult(tuple(path), cost)
        x, y = cur
        for nxt in neighbors4(x, y):
            ec = enter_cost(nxt)
            if ec >= INF_COST:
                continue
            nc = cost + ec
            if nc < best.get(nxt, INF_COST):
                best[nxt] = nc
                parent[nxt] = cur
                heapq.heappush(pq, (nc, nxt))
    return None
