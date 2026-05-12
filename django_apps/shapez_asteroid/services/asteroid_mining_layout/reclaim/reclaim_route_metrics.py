"""P4 reclaim: route cost, zone trace, incremental transport tallies."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.boundary import (
    cells_touching_void,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    INF_COST,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core import (
    mining_priority_route_cell_cost,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_zone import (
    build_route_zone_map,
)


def _path_additional_route_cost(
    path: list[Coord],
    *,
    asteroid_cells: set[Coord],
    mineable_cells: set[Coord],
    buildings: dict[Coord, str],
    transport_cells: dict[Coord, str],
    fixed_stubs: frozenset[Coord],
    outlet_stub: Coord,
) -> int:
    """P4 incremental route가 추가로 소모하는 내부 비용을 계산한다 (§12.2 budget)."""
    if len(path) < 2:
        return 0
    boundary = cells_touching_void(set(asteroid_cells))
    route_tree = {c for c in transport_cells if c != outlet_stub}
    opp: dict[Coord, int] = {}
    route_zone_map = build_route_zone_map(
        asteroid_cells=frozenset(asteroid_cells),
        mineable_cells=frozenset(mineable_cells),
    )
    total = 0
    for i in range(len(path) - 1):
        _frm, to = path[i], path[i + 1]
        ec = mining_priority_route_cell_cost(
            to,
            asteroid_cells=asteroid_cells,
            mineable_cells=mineable_cells,
            boundary_cells=boundary,
            buildings=buildings,
            fixed_stubs=fixed_stubs,
            route_tree=route_tree,
            opportunity_score=opp,
            route_zone_map=route_zone_map,
        )
        if ec >= INF_COST:
            return INF_COST
        total += ec
    return total


def _p4_zone_trace_from_path(
    path: list[Coord],
    *,
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
) -> dict[str, Any]:
    """§12.3 trace: incremental route path; soft key is candidate zone, not promoted corridor."""

    listed = [[int(c[0]), int(c[1])] for c in path]
    soft = [c for c in path if c in mineable and c in asteroid]
    soft_list = [[c[0], c[1]] for c in soft]
    return {
        "p4_reclaim_final_route_cells_added": listed,
        "p4_reclaim_soft_protected_candidate_cells_added": soft_list,
        "p4_reclaim_route_zone_rebuilt": len(path) > 0,
        "p4_reclaim_mineable_excluded_by_route_cells": len(soft),
    }


def _p4_incremental_route_coords_from_commit_trace(tr: Mapping[str, Any]) -> frozenset[Coord]:
    """Parse committed incremental route coordinates from P4-B2 commit trace."""

    out: set[Coord] = set()
    raw = tr.get("p4_reclaim_incremental_route_path_cells")
    if isinstance(raw, list):
        for it in raw:
            if isinstance(it, (list, tuple)) and len(it) == 2:
                x, y = it[0], it[1]
                if isinstance(x, int) and isinstance(y, int) and x != 0:
                    out.add((x, y))
    if not out:
        raw2 = tr.get("p4_reclaim_incremental_route_cells_added")
        if isinstance(raw2, list):
            for it in raw2:
                if isinstance(it, (list, tuple)) and len(it) == 2:
                    x, y = it[0], it[1]
                    if isinstance(x, int) and isinstance(y, int) and x != 0:
                        out.add((x, y))
    return frozenset(out)


def _incremental_internal_transport_on_path(
    path: list[Coord],
    *,
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    existing_transport: frozenset[Coord],
) -> int:
    """P4 route path 중 새로 차지하는 internal transport 수를 계산한다 (§12.2 budget)."""
    n = 0
    for c in path:
        if c in mineable and c in asteroid and c not in existing_transport:
            n += 1
    return n
