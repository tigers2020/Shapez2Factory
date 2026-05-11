"""STEP4 routing failure observability (goal/trunk/blocked/budget classification)."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_routing_permission as _s4_perm,
)

_MAX_NEAREST_TRANSPORT_BFS_VISITS = 50_000


def _neighbor_block_reason(
    n: Coord,
    *,
    stub_cell: Coord,
    want_role: str,
    blocked: frozenset[Coord],
    hard_extras: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    cheap_reuse_cells: frozenset[Coord] | None,
) -> str:
    if n in hard_extras:
        return "hard_protected"
    if n in blocked and n != stub_cell:
        return "blocked"
    if (
        _s4_perm.step4_step_cost(
            n,
            want_role=want_role,
            cells=cells,
            mineable=mineable,
            asteroid=asteroid,
            is_external=is_external,
            cheap_reuse_cells=cheap_reuse_cells,
        )
        is None
    ):
        return "step_cost_none"
    return "ok"


def _nearest_same_kind_transport_hops(
    stub_cell: Coord,
    *,
    want_role: str,
    cells: dict[Coord, dict[str, Any]],
    blocked: frozenset[Coord],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    cheap_reuse_cells: frozenset[Coord] | None,
    transport_cells: set[Coord],
) -> tuple[int | None, Coord | None]:
    targets = frozenset(c for c in transport_cells if c != stub_cell)
    if not targets:
        return None, None

    q: deque[Coord] = deque([stub_cell])
    dist: dict[Coord, int] = {stub_cell: 0}
    visits = 0
    while q:
        c = q.popleft()
        visits += 1
        if visits > _MAX_NEAREST_TRANSPORT_BFS_VISITS:
            return None, None
        d0 = dist[c]
        if c in targets:
            return d0, c
        x, y = c
        for v in neighbors4(x, y):
            if v in blocked and v != stub_cell:
                continue
            if (
                _s4_perm.step4_step_cost(
                    v,
                    want_role=want_role,
                    cells=cells,
                    mineable=mineable,
                    asteroid=asteroid,
                    is_external=is_external,
                    cheap_reuse_cells=cheap_reuse_cells,
                )
                is None
            ):
                continue
            if v not in dist:
                dist[v] = d0 + 1
                q.append(v)
    return None, None


def build_step4_route_failure_detail(
    *,
    placement_id: str | None,
    extractor_cell: Coord,
    stub_cell: Coord,
    transport_kind: str,
    want_role: str,
    blocked: frozenset[Coord],
    hard_extras: frozenset[Coord],
    trunk_cells: frozenset[Coord],
    goal_cells: frozenset[Coord],
    margin_cells: set[Coord],
    transport_now: set[Coord],
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    cheap_reuse_cells: frozenset[Coord] | None,
    search_stats: dict[str, Any],
) -> dict[str, Any]:
    """One failure row: keys match ``step4_route_failure_detail`` trace contract."""

    sx, sy = stub_cell
    near: list[dict[str, Any]] = []
    for n in neighbors4(sx, sy):
        near.append(
            {
                "cell": [int(n[0]), int(n[1])],
                "reason": _neighbor_block_reason(
                    n,
                    stub_cell=stub_cell,
                    want_role=want_role,
                    blocked=blocked,
                    hard_extras=hard_extras,
                    cells=cells,
                    mineable=mineable,
                    asteroid=asteroid,
                    is_external=is_external,
                    cheap_reuse_cells=cheap_reuse_cells,
                ),
            }
        )

    nhops, ncell = _nearest_same_kind_transport_hops(
        stub_cell,
        want_role=want_role,
        cells=cells,
        blocked=blocked,
        mineable=mineable,
        asteroid=asteroid,
        is_external=is_external,
        cheap_reuse_cells=cheap_reuse_cells,
        transport_cells=transport_now,
    )

    stop = search_stats.get("stop_reason")
    if stop == "budget":
        last_error = "no_route_budget"
    elif stop == "exhausted":
        last_error = "no_route_exhausted"
    elif stop == "success":
        last_error = "no_route"
    else:
        # Patched Dijkstra / callers that return ``None`` without populating stats.
        last_error = "no_route"

    ext_goal_ct = len(goal_cells & margin_cells)

    return {
        "placement_id": placement_id,
        "extractor_cell": [int(extractor_cell[0]), int(extractor_cell[1])],
        "stub_cell": [int(stub_cell[0]), int(stub_cell[1])],
        "transport_kind": transport_kind,
        "nearest_existing_transport_distance": nhops,
        "nearest_existing_transport_cell": (
            None if ncell is None else [int(ncell[0]), int(ncell[1])]
        ),
        "existing_trunk_goal_count": len(trunk_cells),
        "external_goal_count": ext_goal_ct,
        "blocked_reason_near_stub": near,
        "search_mode": "goal_cells_union_legacy",
        "expanded_nodes": int(search_stats.get("expanded_nodes", 0)),
        "fallback_reason": None,
        "last_error": last_error,
    }
