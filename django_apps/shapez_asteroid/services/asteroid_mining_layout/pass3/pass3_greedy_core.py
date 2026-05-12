"""Pass3 greedy compression, route probe, anchor pick, map apply.

Pass3 optional **greedy local replacement** (same ``wr`` as the active routing job) mutates only
the in-memory ``transport_cells`` dict: callers adopt the returned dict only after reroute
succeeds. This is **not** P4 §14.3 ``try_atomic_replace_soft_corridor`` on ``mining_map`` (see
``routing.protected_corridor_replace``); that primitive stays in the reclaim layer. Terminology
overlaps (“replacement-first”, no partial commit to caller state) but the contracts differ; see
``_try_greedy_local_replacement_reroute`` and ``foundation.constants`` for Pass3 local replacement
flags.
"""

from __future__ import annotations

import heapq
from collections import deque
from collections.abc import Callable, Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.boundary import (
    cells_touching_void,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    COMMIT_REASON_DEGRADED_CONNECTED_RECOVERY,
    INF_COST,
    P3F_COMMIT_REASON_NORMAL_GAIN,
    PASS3_GREEDY_LOCAL_REPLACEMENT_ENABLED,
    PASS3_GREEDY_LOCAL_REPLACEMENT_MAX_DISCONNECTED_STUBS,
    PASS3_GREEDY_LOCAL_REPLACEMENT_MAX_PATH_LEN,
    PASS3_GREEDY_REJECT_DETAIL_CONNECTIVITY,
    PASS3_GREEDY_REJECT_DETAIL_NO_INTERNAL_DELTA,
    PASS3_GREEDY_REJECT_DETAIL_ZERO_GAIN,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_contracts import (
    Pass3TransportResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.internal_transport_metrics import (  # noqa: E501
    count_internal_transport_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_zone import (
    ROUTE_ZONE_COST,
    RouteZone,
    build_route_zone_map,
    route_zone_for_cell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_trunk_load import (
    cells_on_high_sharing_trunk_edges,
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
    "transport_outlets_disconnected_from_anchor",
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
    route_zone_map: Mapping[Coord, RouteZone] | None = None,
) -> int:
    """Pass3 mining-priority transport reconstruction의 한 칸 route cost를 계산한다.

    Zone scalar는 :data:`ROUTE_ZONE_COST`와 동일 계열이다 (Pass3 lex ``route_step``과 정합).
    ``boundary_cells``는 하위 호환용으로만 받으며, 구역은 ``build_route_zone_map``이 결정한다.

    상세: documents/Algorithm/mining_solver_cursor_sessions/09_step5_pass3_transport.md"""

    _ = boundary_cells
    if cell in buildings:
        return INF_COST
    if cell in fixed_stubs or cell in route_tree:
        return 0
    zm: Mapping[Coord, RouteZone]
    if route_zone_map is not None:
        zm = route_zone_map
    else:
        zm = build_route_zone_map(
            asteroid_cells=frozenset(asteroid_cells),
            mineable_cells=frozenset(mineable_cells),
        )
    base = ROUTE_ZONE_COST[route_zone_for_cell(cell, zm)]
    if cell in mineable_cells:
        base += opportunity_score.get(cell, 0)
    return base


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


def transport_outlets_disconnected_from_anchor(
    transport_cells: dict[Coord, str],
    *,
    outlets_order: list[Coord],
    anchor: Coord,
    limit: int = 5,
) -> list[Coord]:
    """Outlets not reachable from ``anchor`` via cardinal transport edges (BFS ``seen``).

    Preconditions match :func:`transport_connects_outlets_to_anchor` (anchor and outlets in graph).
    """

    required = frozenset(outlets_order)
    if anchor not in transport_cells or not required or not required.issubset(transport_cells):
        return []
    q: deque[Coord] = deque([anchor])
    seen: set[Coord] = {anchor}
    while q:
        cur = q.popleft()
        for nxt in _transport_adjacent(cur, transport_cells):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    out: list[Coord] = []
    for o in outlets_order:
        if o not in seen:
            out.append(o)
            if len(out) >= limit:
                break
    return out


def _pass3_connectivity_reject_sample_dict(
    *,
    victim: Coord,
    anchor: Coord,
    tc_before_trial: dict[Coord, str],
    trial: dict[Coord, str],
    outlets_order: list[Coord],
) -> dict[str, Any]:
    disc = transport_outlets_disconnected_from_anchor(
        trial,
        outlets_order=outlets_order,
        anchor=anchor,
        limit=8,
    )
    return {
        "victim_cell": [victim[0], victim[1]],
        "affected_stub_count": len(disc),
        "disconnected_stub_samples": [[c[0], c[1]] for c in disc],
        "nearest_anchor_distance": abs(victim[0] - anchor[0]) + abs(victim[1] - anchor[1]),
        "transport_cell_count_before_trial": len(tc_before_trial),
        "transport_cell_count_after_trial": len(trial),
    }


def _new_pass3_greedy_local_replacement_stats() -> dict[str, Any]:
    """NDJSON-friendly counters for optional delete + local same-kind reroute (Pass3 greedy).

    Semantics (telemetry contract):

    * ``attempted_count`` — :func:`_try_greedy_local_replacement_reroute` entered (one victim’s
      reroute evaluation started).
    * ``accepted_count`` — reroute returned a ``merged`` dict that the caller adopted: outlets
      reach ``anchor``, only ``wr`` cells were added on probe paths, and **internal** transport
      count (per ``is_external``) **strictly decreased** vs ``pre_delete_tc``. Same instant as
      caller ``tc`` update; not a pre-check “looks good”.
    * ``rejected_by_*`` — reroute returned ``None``; the caller’s transport dict for that attempt
      is unchanged (no partial commit).
    """

    return {
        "enabled": bool(PASS3_GREEDY_LOCAL_REPLACEMENT_ENABLED),
        "attempted_count": 0,
        "accepted_count": 0,
        "rejected_by_path_len": 0,
        "rejected_by_disconnected_stub_limit": 0,
        "rejected_by_no_path": 0,
        "rejected_by_no_net_internal_gain": 0,
    }


def _try_greedy_local_replacement_reroute(
    pre_delete_tc: dict[Coord, str],
    trial: dict[Coord, str],
    *,
    wr: str,
    anchor: Coord,
    outlets_order: list[Coord],
    mineable_cells: set[Coord],
    asteroid_cells: set[Coord],
    buildings: dict[Coord, str],
    is_external: Callable[[Coord], bool],
    stats: dict[str, Any],
) -> dict[Coord, str] | None:
    """If enabled, add same-kind ``wr`` along stub→anchor probe paths until connected.

    **Caller atomicity:** returns ``None`` on any reject; only a full success returns ``merged``.
    The caller must not merge partial state (see ``rejected_by_*`` counters).

    **Internal transport:** ``accepted_count`` increments only when
    ``count_internal_transport_cells(merged) < count_internal_transport_cells(pre_delete_tc)``.
    If the graph connects but that strict inequality fails, increments
    ``rejected_by_no_net_internal_gain`` and returns ``None``.

    **§14.3:** This path does not read soft/hard protected corridors on ``mining_map``; it is the
    Pass3 ``transport_cells`` compression helper. P4 §14.3 remains
    ``try_atomic_replace_soft_corridor``.

    ``rejected_by_disconnected_stub_limit`` — disconnected outlet stubs from anchor exceed
    :data:`PASS3_GREEDY_LOCAL_REPLACEMENT_MAX_DISCONNECTED_STUBS` (per-attempt budget), or the BFS
    limit branch fired with an empty/oversized disconnect set.
    """

    if not PASS3_GREEDY_LOCAL_REPLACEMENT_ENABLED:
        return None
    stats["attempted_count"] = int(stats["attempted_count"]) + 1
    before_i = count_internal_transport_cells(pre_delete_tc.keys(), is_external=is_external)
    merged = dict(trial)
    for _ in range(PASS3_GREEDY_LOCAL_REPLACEMENT_MAX_DISCONNECTED_STUBS + 2):
        if transport_connects_outlets_to_anchor(
            merged,
            outlets_order=outlets_order,
            anchor=anchor,
        ):
            after_i = count_internal_transport_cells(merged.keys(), is_external=is_external)
            if before_i > after_i:
                stats["accepted_count"] = int(stats["accepted_count"]) + 1
                return merged
            stats["rejected_by_no_net_internal_gain"] = (
                int(stats["rejected_by_no_net_internal_gain"]) + 1
            )
            return None
        disc = transport_outlets_disconnected_from_anchor(
            merged,
            outlets_order=outlets_order,
            anchor=anchor,
            limit=PASS3_GREEDY_LOCAL_REPLACEMENT_MAX_DISCONNECTED_STUBS + 1,
        )
        if not disc or len(disc) > PASS3_GREEDY_LOCAL_REPLACEMENT_MAX_DISCONNECTED_STUBS:
            # Budget: at most MAX_DISCONNECTED_STUBS stubs may need patching per victim attempt.
            stats["rejected_by_disconnected_stub_limit"] = (
                int(stats["rejected_by_disconnected_stub_limit"]) + 1
            )
            return None
        stub = disc[0]
        path = placement_stub_route_probe_path(
            outlet_stub=stub,
            anchor=anchor,
            asteroid_cells=asteroid_cells,
            mineable_cells=mineable_cells,
            buildings=buildings,
            transport_cells=merged,
            fixed_stubs=frozenset(outlets_order),
        )
        if path is None:
            stats["rejected_by_no_path"] = int(stats["rejected_by_no_path"]) + 1
            return None
        if len(path) > PASS3_GREEDY_LOCAL_REPLACEMENT_MAX_PATH_LEN:
            stats["rejected_by_path_len"] = int(stats["rejected_by_path_len"]) + 1
            return None
        for cell in path:
            merged[cell] = wr
    return None


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
    layout_role: str,
    buildings: dict[Coord, str],
    lr_stats: dict[str, Any],
    is_external: Callable[[Coord], bool] | None = None,
    skip_victim_cells: frozenset[Coord] | None = None,
) -> tuple[dict[Coord, str], int, str | None, dict[str, Any] | None]:
    """transport 셀 하나를 제거해 stub connectivity가 유지되는지 시험한다.

    §11 Pass3 compression 맥락이다.
    세 번째 반환값: 제거 실패 시 ``pass3_greedy_reject_detail`` 후보(성공 시 ``None``).
    넷째: 첫 connectivity-only 실패 시 ``pass3_connectivity_reject_sample`` (성공 시 ``None``).
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
    if not cands:
        return tc, 0, PASS3_GREEDY_REJECT_DETAIL_NO_INTERNAL_DELTA, None
    any_unskipped_attempt = False
    first_connectivity_sample: dict[str, Any] | None = None
    for victim in cands:
        if skip_victim_cells and victim in skip_victim_cells:
            continue
        any_unskipped_attempt = True
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
        if is_external is not None:
            rerouted = _try_greedy_local_replacement_reroute(
                tc,
                trial,
                wr=layout_role,
                anchor=anchor,
                outlets_order=outlets_order,
                mineable_cells=mineable_cells,
                asteroid_cells=asteroid_cells,
                buildings=buildings,
                is_external=is_external,
                stats=lr_stats,
            )
            if rerouted is not None:
                tc = rerouted
                break
        if first_connectivity_sample is None:
            first_connectivity_sample = _pass3_connectivity_reject_sample_dict(
                victim=victim,
                anchor=anchor,
                tc_before_trial=tc,
                trial=trial,
                outlets_order=outlets_order,
            )
    else:
        if not any_unskipped_attempt:
            return tc, 0, PASS3_GREEDY_REJECT_DETAIL_NO_INTERNAL_DELTA, None
        return tc, 0, PASS3_GREEDY_REJECT_DETAIL_CONNECTIVITY, first_connectivity_sample
    after = len(
        _interior_transport_candidates(
            tc,
            mineable_cells=mineable_cells,
            outlets_order=outlets_order,
            anchor=anchor,
        )
    )
    gain_spine = max(0, before - after)
    if is_external is not None:
        bi0 = count_internal_transport_cells(transport_cells.keys(), is_external=is_external)
        ai0 = count_internal_transport_cells(tc.keys(), is_external=is_external)
        gain_internal = max(0, bi0 - ai0)
        gain = max(gain_spine, gain_internal)
    else:
        gain = gain_spine
    return tc, gain, None, None


def _compress_transport_greedy(
    transport_cells: dict[Coord, str],
    *,
    mineable_cells: set[Coord],
    asteroid_cells: set[Coord],
    outlets_order: list[Coord],
    anchor: Coord,
    layout_role: str,
    buildings: dict[Coord, str],
    lr_stats: dict[str, Any],
    is_external: Callable[[Coord], bool] | None = None,
    skip_victim_cells: frozenset[Coord] | None = None,
) -> tuple[dict[Coord, str], int, str, dict[str, Any] | None]:
    """고정 output stub을 보존하며 불필요한 transport를 greedy로 제거한다 (§11 Pass3 transport)."""
    tc = dict(transport_cells)
    gain_total = 0
    last_fail_detail = PASS3_GREEDY_REJECT_DETAIL_ZERO_GAIN
    first_connectivity_sample: dict[str, Any] | None = None
    while True:
        tc_next, gain, fail_detail, conn_s = _try_remove_one_transport_cell(
            tc,
            mineable_cells=mineable_cells,
            asteroid_cells=asteroid_cells,
            outlets_order=outlets_order,
            anchor=anchor,
            layout_role=layout_role,
            buildings=buildings,
            lr_stats=lr_stats,
            is_external=is_external,
            skip_victim_cells=skip_victim_cells,
        )
        if conn_s is not None and first_connectivity_sample is None:
            first_connectivity_sample = conn_s
        if gain == 0:
            if fail_detail is not None:
                last_fail_detail = fail_detail
            break
        tc = tc_next
        gain_total += gain
    return tc, gain_total, last_fail_detail, first_connectivity_sample


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
    trunk_load: dict[str, Any] | None = None,
    recovery_skip_high_sharing_transport_removals: bool = False,
    is_external: Callable[[Coord], bool] | None = None,
) -> Pass3TransportResult:
    """Remove redundant interior transport while preserving stub→anchor connectivity."""

    _ = transport_role
    metrics_base: dict[str, Any] = {"over_capacity_segments": 0, "bottleneck_count": 0}
    lr_stats = _new_pass3_greedy_local_replacement_stats()
    metrics_base["pass3_greedy_local_replacement"] = lr_stats
    skip_victims: frozenset[Coord] | None = None
    if recovery_skip_high_sharing_transport_removals and isinstance(trunk_load, dict):
        skip_victims = cells_on_high_sharing_trunk_edges(trunk_load, transport_kind=transport_role)
        if skip_victims:
            metrics_base["pass3_recovery_skip_high_sharing_cell_count"] = len(skip_victims)

    layout_role = next(iter(transport_cells.values())) if transport_cells else "belt"
    new_cells, gain_total, greedy_reject_detail, connectivity_sample = _compress_transport_greedy(
        transport_cells,
        mineable_cells=mineable_cells,
        asteroid_cells=asteroid_cells,
        outlets_order=outlets_order,
        anchor=anchor,
        layout_role=layout_role,
        buildings=buildings,
        lr_stats=lr_stats,
        is_external=is_external,
        skip_victim_cells=skip_victims,
    )
    if connectivity_sample is not None and gain_total == 0:
        metrics_base["pass3_connectivity_reject_sample"] = connectivity_sample

    if gain_total > 0:
        return Pass3TransportResult(
            True,
            new_cells,
            {**metrics_base, "commit_reason": P3F_COMMIT_REASON_NORMAL_GAIN, "gain": gain_total},
        )

    if gain_total == 0 and allow_degraded_connected_commit:
        return Pass3TransportResult(
            True,
            dict(transport_cells),
            {
                **metrics_base,
                "commit_reason": COMMIT_REASON_DEGRADED_CONNECTED_RECOVERY,
                "gain": 0,
                "pass3_greedy_reject_detail": greedy_reject_detail,
            },
        )

    return Pass3TransportResult(
        False,
        dict(transport_cells),
        {
            **metrics_base,
            "rejected_reason": "rejected_by_gain_or_length",
            "gain": 0,
            "pass3_greedy_reject_detail": greedy_reject_detail,
        },
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
    route_zone_map = build_route_zone_map(
        asteroid_cells=frozenset(asteroid_cells),
        mineable_cells=frozenset(mineable_cells),
    )

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
            route_zone_map=route_zone_map,
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
