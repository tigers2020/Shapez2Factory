"""Pass3 greedy compression, route probe, anchor pick, map apply."""

from __future__ import annotations

import heapq
from collections import deque
from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.boundary import (
    cells_touching_void,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    INF_COST,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_contracts import (
    Pass3TransportResult,
)

__all__ = [
    "Pass3TransportResult",
    "mining_map_after_transport_reconstruction",
    "mining_priority_route_cell_cost",
    "pick_pass3_anchor_transport_cell",
    "placement_stub_route_probe_path",
    "placement_stub_route_to_trunk_feasible",
    "reconstruct_mining_priority_transport",
    "transport_connects_outlets_to_anchor",
]


def mining_priority_route_cell_cost(
    cell: Coord,
    *,
    asteroid_cells: set[Coord],
    mineable_cells: set[Coord],
    boundary_cells: set[Coord],
    buildings: dict[Coord, str],
    fixed_stubs: frozenset[Coord],
    route_tree: set[Coord],
    opportunity_score: dict[Coord, int],
) -> int:
    """Pass3 mining-priority transport reconstruction의 한 칸 route cost를 계산한다.

        mineable 내부 transport는 높은 비용으로 밀어낸다 (§11 STEP5 Pass3 transport).

    상세: documents/Algorithm/mining_solver_cursor_sessions/09_step5_pass3_transport.md"""
    if cell in buildings:
        return INF_COST
    if cell in fixed_stubs or cell in route_tree:
        return 0
    if cell not in asteroid_cells:
        return 1
    if cell not in mineable_cells:
        return 60
    opp = opportunity_score.get(cell, 0)
    if cell in boundary_cells:
        return 120 + 20 + opp
    return 120 + 80 + opp


def _transport_adjacent(cell: Coord, transport_cells: dict[Coord, str]) -> list[Coord]:
    """Cardinal neighbors that share an edge in display coordinates (belt continuity)."""

    x, y = cell
    return [n for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if n in transport_cells]


def _cardinal_neighbors(cur: Coord) -> tuple[Coord, ...]:
    """x==0 없는 blueprint grid 규칙으로 cardinal 이웃을 순회한다 (§11 Pass3 transport)."""
    x, y = cur
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


def transport_connects_outlets_to_anchor(
    transport_cells: dict[Coord, str],
    *,
    outlets_order: list[Coord],
    anchor: Coord,
    mineable_cells: set[Coord] | None = None,
    asteroid_cells: set[Coord] | None = None,
) -> bool:
    """True iff **every** outlet in ``outlets_order`` reaches ``anchor`` via cardinal transport.

    ``mineable_cells`` / ``asteroid_cells`` are accepted for call-site compatibility; they are
    not used (Pass3 commit must not treat void gaps as belt/pipe continuity).
    """

    _ = mineable_cells
    _ = asteroid_cells
    required = frozenset(outlets_order)
    if anchor not in transport_cells:
        return False
    if not required:
        return False
    if not required.issubset(transport_cells):
        return False

    q: deque[Coord] = deque([anchor])
    seen: set[Coord] = {anchor}
    while q:
        cur = q.popleft()
        for nxt in _transport_adjacent(cur, transport_cells):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)

    return required.issubset(seen)


def _interior_transport_candidates(
    transport_cells: dict[Coord, str],
    *,
    mineable_cells: set[Coord],
    outlets_order: list[Coord],
    anchor: Coord,
) -> list[Coord]:
    """Cells eligible for removal (everything except outlets and anchor).

    ``mineable_cells`` is used only for prioritization: prefer removing tiles inside mineable.
    """

    blocked = frozenset(outlets_order) | {anchor}
    return [c for c in transport_cells if c not in blocked]


def _try_remove_one_transport_cell(
    transport_cells: dict[Coord, str],
    *,
    mineable_cells: set[Coord],
    asteroid_cells: set[Coord],
    outlets_order: list[Coord],
    anchor: Coord,
) -> tuple[dict[Coord, str], int]:
    """transport 셀 하나를 제거해 stub connectivity가 유지되는지 시험한다.

    §11 Pass3 compression 맥락이다.
    """
    before = len(
        _interior_transport_candidates(
            transport_cells,
            mineable_cells=mineable_cells,
            outlets_order=outlets_order,
            anchor=anchor,
        )
    )
    tc = dict(transport_cells)
    cands = _interior_transport_candidates(
        tc,
        mineable_cells=mineable_cells,
        outlets_order=outlets_order,
        anchor=anchor,
    )
    cands.sort(
        key=lambda c: (
            0 if c in mineable_cells else 1,
            -(abs(c[0] - anchor[0]) + abs(c[1] - anchor[1])),
        ),
    )
    for victim in cands:
        trial = {k: v for k, v in tc.items() if k != victim}
        if transport_connects_outlets_to_anchor(
            trial,
            outlets_order=outlets_order,
            anchor=anchor,
            mineable_cells=mineable_cells,
            asteroid_cells=asteroid_cells,
        ):
            tc = trial
            break
    after = len(
        _interior_transport_candidates(
            tc,
            mineable_cells=mineable_cells,
            outlets_order=outlets_order,
            anchor=anchor,
        )
    )
    return tc, max(0, before - after)


def _compress_transport_greedy(
    transport_cells: dict[Coord, str],
    *,
    mineable_cells: set[Coord],
    asteroid_cells: set[Coord],
    outlets_order: list[Coord],
    anchor: Coord,
) -> tuple[dict[Coord, str], int]:
    """고정 output stub을 보존하며 불필요한 transport를 greedy로 제거한다 (§11 Pass3 transport)."""
    tc = dict(transport_cells)
    gain_total = 0
    while True:
        tc_next, gain = _try_remove_one_transport_cell(
            tc,
            mineable_cells=mineable_cells,
            asteroid_cells=asteroid_cells,
            outlets_order=outlets_order,
            anchor=anchor,
        )
        if gain == 0:
            break
        tc = tc_next
        gain_total += gain
    return tc, gain_total


def reconstruct_mining_priority_transport(
    *,
    anchor: Coord,
    asteroid_cells: set[Coord],
    mineable_cells: set[Coord],
    buildings: dict[Coord, str],
    transport_cells: dict[Coord, str],
    outlets_order: list[Coord],
    transport_role: str,
    allow_degraded_connected_commit: bool = False,
) -> Pass3TransportResult:
    """Remove redundant interior transport while preserving stub→anchor connectivity."""

    _ = buildings
    _ = transport_role
    metrics_base: dict[str, Any] = {"over_capacity_segments": 0, "bottleneck_count": 0}

    new_cells, gain_total = _compress_transport_greedy(
        transport_cells,
        mineable_cells=mineable_cells,
        asteroid_cells=asteroid_cells,
        outlets_order=outlets_order,
        anchor=anchor,
    )

    if gain_total > 0:
        return Pass3TransportResult(
            True,
            new_cells,
            {**metrics_base, "commit_reason": "normal_gain", "gain": gain_total},
        )

    if gain_total == 0 and allow_degraded_connected_commit:
        return Pass3TransportResult(
            True,
            dict(transport_cells),
            {**metrics_base, "commit_reason": "degraded_connected_recovery", "gain": 0},
        )

    return Pass3TransportResult(
        False,
        dict(transport_cells),
        {**metrics_base, "rejected_reason": "rejected_by_gain_or_length", "gain": 0},
    )


def placement_stub_route_probe_path(
    *,
    outlet_stub: Coord,
    anchor: Coord,
    asteroid_cells: set[Coord],
    mineable_cells: set[Coord],
    buildings: dict[Coord, str],
    transport_cells: dict[Coord, str],
    fixed_stubs: frozenset[Coord],
) -> list[Coord] | None:
    """Shortest cardinal path stub→anchor using mining-priority costs (Pass3 stack)."""

    boundary = cells_touching_void(set(asteroid_cells))
    route_tree = {c for c in transport_cells if c != outlet_stub}
    opp: dict[Coord, int] = {}

    def edge_cost(frm: Coord, to: Coord) -> int:
        """placement stub probe에서 mineable 통과 비용을 계산한다 (§11 Pass3 route probe)."""
        _ = frm
        return mining_priority_route_cell_cost(
            to,
            asteroid_cells=asteroid_cells,
            mineable_cells=mineable_cells,
            boundary_cells=boundary,
            buildings=buildings,
            fixed_stubs=fixed_stubs,
            route_tree=route_tree,
            opportunity_score=opp,
        )

    pq: list[tuple[int, Coord]] = [(0, outlet_stub)]
    best: dict[Coord, int] = {outlet_stub: 0}
    parent: dict[Coord, Coord | None] = {outlet_stub: None}
    while pq:
        cost, cur = heapq.heappop(pq)
        if cost != best.get(cur, INF_COST):
            continue
        if cur == anchor:
            path: list[Coord] = []
            walk: Coord | None = cur
            while walk is not None:
                path.append(walk)
                walk = parent.get(walk)
            path.reverse()
            return path
        x, y = cur
        for nxt in _cardinal_neighbors((x, y)):
            ec = edge_cost(cur, nxt)
            if ec >= INF_COST:
                continue
            nc = cost + ec
            if nc < best.get(nxt, INF_COST):
                best[nxt] = nc
                parent[nxt] = cur
                heapq.heappush(pq, (nc, nxt))
    return None


def placement_stub_route_to_trunk_feasible(
    *,
    outlet_stub: Coord,
    anchor: Coord,
    asteroid_cells: set[Coord],
    mineable_cells: set[Coord],
    buildings: dict[Coord, str],
    transport_cells: dict[Coord, str],
    fixed_stubs: frozenset[Coord],
) -> bool:
    """placement stub이 trunk/external로 이어지는지 route probe로 확인한다.

        Pass3 rescan bundle commit의 safety gate다 (§11 STEP5 Pass3 transport).

    상세: documents/Algorithm/mining_solver_cursor_sessions/09_step5_pass3_transport.md"""
    return (
        placement_stub_route_probe_path(
            outlet_stub=outlet_stub,
            anchor=anchor,
            asteroid_cells=asteroid_cells,
            mineable_cells=mineable_cells,
            buildings=buildings,
            transport_cells=transport_cells,
            fixed_stubs=fixed_stubs,
        )
        is not None
    )


def mining_map_after_transport_reconstruction(
    mining_map: list[dict[str, Any]],
    new_transport: dict[Coord, str],
    *,
    target_role: str,
) -> list[dict[str, Any]]:
    """Apply ``new_transport`` only to cells whose row role is ``target_role`` (belt or pipe).

    Other transport kinds on the map are left unchanged so Pass3 for one kind cannot strip
    belts/pipes of the other kind.
    """

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        cells_dict_from_mining_map,
    )

    cells = {k: dict(v) for k, v in cells_dict_from_mining_map(mining_map).items()}
    for c in list(cells.keys()):
        row = cells[c]
        if row.get("role") != target_role:
            continue
        if c not in new_transport:
            del cells[c]
        else:
            row["role"] = new_transport[c]
            cells[c] = row
    ordered = sorted(cells.keys(), key=lambda p: (p[1], p[0]))
    return [dict(cells[k]) for k in ordered]


def pick_pass3_anchor_transport_cell(
    cells: dict[Coord, dict[str, Any]],
    *,
    want_role: str,
    is_external: Callable[[Coord], bool],
) -> Coord | None:
    """Choose a trunk-facing transport tile adjacent to ``is_external`` (prefer east)."""

    hits: list[Coord] = []
    for c, row in cells.items():
        if row.get("role") != want_role:
            continue
        x, y = c
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if is_external((nx, ny)):
                hits.append(c)
                break
    if not hits:
        return None
    hits.sort(key=lambda p: (-p[0], p[1]))
    return hits[0]
