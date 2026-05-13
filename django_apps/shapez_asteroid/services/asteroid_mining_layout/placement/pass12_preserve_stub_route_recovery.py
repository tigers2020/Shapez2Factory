"""Pass12 merged-seed: NEAR_TRANSPORT missing-stub route recovery (pure probe).

``try_preserve_stub_route_recovery`` does **not** mutate ``Pass12LayoutScratch``; callers
commit ``new_transport_coords`` on success only.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import shape_miner_output_cell
from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_PASS12_STUB_ROUTE_RECOVERY_NEAREST_HOPS,
    MAX_PASS12_STUB_ROUTE_RECOVERY_NEW_TRANSPORT_CELLS,
    MAX_PASS12_STUB_ROUTE_RECOVERY_PATH_LEN,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTENSIONS,
    EXTRACTORS_FLUID,
    EXTRACTORS_SHAPE,
    layout_kind,
    want_role,
)


def existing_same_kind_transport_cells_from_map(
    cells: dict[Coord, dict[str, Any]],
    *,
    want_wr: str,
) -> frozenset[Coord]:
    """Cells in ``cells`` whose mining-map ``role`` matches ``want_wr`` (``belt`` / ``pipe``)."""

    return frozenset(c for c, row in cells.items() if row.get("role") == want_wr)


def scratch_same_kind_goal_cells(
    scratch_transport_cells: frozenset[Coord],
    *,
    cells: dict[Coord, dict[str, Any]],
    want_wr: str,
) -> frozenset[Coord]:
    """Scratch coords usable as same-kind goals: exclude wrong-role rows when present on map."""

    out: list[Coord] = []
    for c in scratch_transport_cells:
        row = cells.get(c)
        if row is None:
            out.append(c)
            continue
        role = row.get("role")
        if role == want_wr:
            out.append(c)
    return frozenset(out)


def goal_transport_cells(
    *,
    cells: dict[Coord, dict[str, Any]],
    want_wr: str,
    scratch_transport_cells: frozenset[Coord],
) -> frozenset[Coord]:
    """BFS goal set: existing same-role rows plus scratch transport that matches ``want_wr``."""

    return existing_same_kind_transport_cells_from_map(
        cells, want_wr=want_wr
    ) | scratch_same_kind_goal_cells(scratch_transport_cells, cells=cells, want_wr=want_wr)


@dataclass(frozen=True)
class StubRouteRecoveryResult:
    accepted: bool
    trace: dict[str, Any]
    new_transport_coords: frozenset[Coord]
    chosen_r: int | None
    stub_cell: Coord | None


def _other_transport_role(want_wr: str) -> str:
    return "belt" if want_wr == "pipe" else "pipe"


def _rotation_order(raw_r: Any) -> list[int]:
    order: list[int] = []
    if isinstance(raw_r, int):
        order.append(raw_r % 4)
    for r in range(4):
        if r not in order:
            order.append(r)
    return order


def _stub_cell_recovery_priority(
    stub_cell: Coord,
    cells: dict[Coord, dict[str, Any]],
) -> tuple[int, int, int]:
    """Sort key: void, inferred, asteroid_field, then other stub contexts."""

    row = cells.get(stub_cell)
    if row is None:
        return (0, stub_cell[1], stub_cell[0])
    role = row.get("role")
    if role == "inferred":
        return (1, stub_cell[1], stub_cell[0])
    if role == "occupied" and layout_kind(row) == "asteroid_field":
        return (2, stub_cell[1], stub_cell[0])
    return (3, stub_cell[1], stub_cell[0])


def _stub_space_mvp(
    stub_cell: Coord,
    *,
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    blocked_body: frozenset[Coord],
    want_wr: str,
) -> tuple[bool, str | None]:
    """MVP: inferred / void mineable / ``asteroid_field`` only; no extension carve."""

    row0 = cells.get(stub_cell)
    if row0 is not None and row0.get("role") == "occupied":
        lk0 = layout_kind(row0) or ""
        if lk0 in EXTENSIONS:
            return False, "extension_carve_disabled"
    if stub_cell in blocked_body:
        return False, "blocked"
    if stub_cell not in mineable:
        return False, "not_mineable"
    row = cells.get(stub_cell)
    if row is None:
        return True, None
    role = row.get("role")
    if role == "inferred":
        return True, None
    if role == want_wr:
        return False, "already_same_kind_transport"
    if role == _other_transport_role(want_wr):
        return False, "mixed_kind_at_stub"
    if role == "occupied":
        lk = layout_kind(row) or ""
        if lk in EXTENSIONS:
            return False, "extension_carve_disabled"
        if lk == "asteroid_field":
            return True, None
        if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
            return False, "extractor_at_stub"
        return False, "occupied_not_stub_space"
    return False, "unsupported_role"


def _step_block_reason(
    nxt: Coord,
    *,
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    blocked_body: frozenset[Coord],
    want_wr: str,
    goal_transport_cells: frozenset[Coord],
) -> str | None:
    """None iff stub-route BFS may enter ``nxt`` (preserve stub recovery step feasibility)."""

    if nxt in blocked_body:
        return "blocked_body"
    if nxt in goal_transport_cells:
        return None
    if nxt not in mineable:
        return "not_mineable"
    row = cells.get(nxt)
    if row is None:
        return None
    role = row.get("role")
    if role == want_wr:
        return None
    if role == _other_transport_role(want_wr):
        return "wrong_kind_transport"
    if role == "inferred":
        return None
    if role == "occupied":
        lk = layout_kind(row) or ""
        if lk == "asteroid_field":
            return None
        return "occupied_not_traversable"
    return "unsupported_role"


def _bump_reason(counts: dict[str, int], key: str) -> None:
    counts[key] = counts.get(key, 0) + 1


def _reachable_goals_under_edge_cap(
    start: Coord,
    *,
    goal_transport_cells: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    blocked_body: frozenset[Coord],
    want_wr: str,
    max_edges: int,
    max_visits: int,
) -> int:
    """How many goal cells share a ``_step_block_reason``-compatible component within depth cap."""

    if start in goal_transport_cells:
        return 1
    parent: dict[Coord, Coord | None] = {start: None}
    dist_edges: dict[Coord, int] = {start: 0}
    q: deque[Coord] = deque([start])
    visits = 0
    while q:
        cur = q.popleft()
        visits += 1
        if visits > max_visits:
            break
        d0 = dist_edges[cur]
        x, y = cur
        for nxt in sorted(neighbors4(x, y), key=lambda p: (p[1], p[0])):
            if nxt in parent:
                continue
            if (
                _step_block_reason(
                    nxt,
                    cells=cells,
                    mineable=mineable,
                    blocked_body=blocked_body,
                    want_wr=want_wr,
                    goal_transport_cells=goal_transport_cells,
                )
                is not None
            ):
                continue
            nd = d0 + 1
            if nd > max_edges:
                continue
            parent[nxt] = cur
            dist_edges[nxt] = nd
            q.append(nxt)
    return len(goal_transport_cells & frozenset(parent.keys()))


def _local_neighbor_cells_around_stub(
    stub: Coord,
    cells: dict[Coord, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Cardinal neighbors of ``stub`` for drop NDJSON (bounded, deterministic order)."""

    x, y = stub
    out: list[dict[str, Any]] = []
    for nx in sorted(neighbors4(x, y), key=lambda p: (p[1], p[0])):
        row = cells.get(nx)
        lk = layout_kind(row) if row is not None else None
        out.append(
            {
                "cell": [int(nx[0]), int(nx[1])],
                "role": row.get("role") if row else None,
                "layout_kind": lk,
            }
        )
    return out


def _bfs_shortest_path(
    start: Coord,
    *,
    goal_transport_cells: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    blocked_body: frozenset[Coord],
    want_wr: str,
    max_edges: int,
) -> tuple[list[Coord] | None, dict[str, Any]]:
    """Shortest path by edge count; deterministic tie-break via sorted neighbor expansion."""

    if start in goal_transport_cells:
        return [start], {
            "failure": None,
            "path_cell_count": 1,
            "route_len_edges": 0,
            "expanded_nodes": 1,
            "blocked_frontier_reason_counts": {},
            "last_frontier_sample": [[int(start[0]), int(start[1])]],
        }

    parent: dict[Coord, Coord | None] = {start: None}
    dist_edges: dict[Coord, int] = {start: 0}
    q: deque[Coord] = deque([start])
    visits = 0
    blocked_frontier_reason_counts: dict[str, int] = {}
    recent_expanded: deque[list[int]] = deque(maxlen=4)
    while q:
        cur = q.popleft()
        visits += 1
        recent_expanded.append([int(cur[0]), int(cur[1])])
        if visits > 50_000:
            return None, {
                "failure": "visit_cap",
                "visited": visits,
                "expanded_nodes": len(parent),
                "blocked_frontier_reason_counts": dict(
                    sorted(blocked_frontier_reason_counts.items(), key=lambda kv: kv[0])
                ),
                "last_frontier_sample": list(sorted(recent_expanded, key=lambda p: (p[1], p[0]))),
            }
        d0 = dist_edges[cur]
        x, y = cur
        for nxt in sorted(neighbors4(x, y), key=lambda p: (p[1], p[0])):
            if nxt in parent:
                continue
            br = _step_block_reason(
                nxt,
                cells=cells,
                mineable=mineable,
                blocked_body=blocked_body,
                want_wr=want_wr,
                goal_transport_cells=goal_transport_cells,
            )
            if br is not None:
                _bump_reason(blocked_frontier_reason_counts, br)
                continue
            nd = d0 + 1
            if nd > max_edges:
                _bump_reason(blocked_frontier_reason_counts, "exceeds_max_edges_cap")
                continue
            parent[nxt] = cur
            dist_edges[nxt] = nd
            if nxt in goal_transport_cells:
                path: list[Coord] = []
                w: Coord | None = nxt
                while w is not None:
                    path.append(w)
                    w = parent.get(w)
                path.reverse()
                edges = len(path) - 1
                return path, {
                    "failure": None,
                    "path_cell_count": len(path),
                    "route_len_edges": edges,
                    "expanded_nodes": len(parent),
                    "blocked_frontier_reason_counts": dict(
                        sorted(blocked_frontier_reason_counts.items(), key=lambda kv: kv[0])
                    ),
                    "last_frontier_sample": list(
                        sorted(recent_expanded, key=lambda p: (p[1], p[0]))
                    ),
                }
            q.append(nxt)
    return None, {
        "failure": "no_same_kind_route",
        "expanded_nodes": len(parent),
        "blocked_frontier_reason_counts": dict(
            sorted(blocked_frontier_reason_counts.items(), key=lambda kv: kv[0])
        ),
        "last_frontier_sample": list(sorted(recent_expanded, key=lambda p: (p[1], p[0]))),
    }


def _empty_psr(nearest_hops: int | None) -> dict[str, Any]:
    return {
        "attempted": True,
        "accepted": False,
        "rejected_reason": None,
        "candidate_rotation_count": 0,
        "selected_r": None,
        "selected_stub_cell": None,
        "path_cell_count": None,
        "route_len_edges": None,
        "path_cells": None,
        "nearest_same_kind_transport_hops": nearest_hops,
    }


def try_preserve_stub_route_recovery(
    *,
    miner: Coord,
    extensions: frozenset[Coord],
    transport_kind: str,
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    scratch_transport_cells: frozenset[Coord],
    scratch_blocked_cells: frozenset[Coord],
    nearest_same_kind_transport_hops: int | None,
    row_r_raw: Any,
    nearest_same_kind_transport_cell: Coord | None = None,
) -> StubRouteRecoveryResult:
    """Pure probe: same-kind trunk reachable from an inferred/empty output stub (MVP)."""

    psr = _empty_psr(nearest_same_kind_transport_hops)
    base_trace: dict[str, Any] = {"preserve_stub_recovery": psr}
    psr["miner_cell"] = [int(miner[0]), int(miner[1])]
    psr["transport_kind"] = transport_kind
    psr["nearest_same_kind_transport_cell"] = (
        None
        if nearest_same_kind_transport_cell is None
        else [
            int(nearest_same_kind_transport_cell[0]),
            int(nearest_same_kind_transport_cell[1]),
        ]
    )
    try:
        want_wr = want_role(transport_kind)
    except ValueError:
        psr["attempted"] = False
        psr["rejected_reason"] = "rejected_by_invalid_want_role"
        psr["scratch_transport_input_count"] = len(scratch_transport_cells)
        psr["scratch_goal_count"] = 0
        psr["scratch_goal_without_map_row_count"] = 0
        psr["scratch_goal_wrong_role_excluded_count"] = 0
        return StubRouteRecoveryResult(
            accepted=False,
            trace=base_trace,
            new_transport_coords=frozenset(),
            chosen_r=None,
            stub_cell=None,
        )

    without_map = 0
    wrong_role_excluded = 0
    for c in scratch_transport_cells:
        row = cells.get(c)
        if row is None:
            without_map += 1
        elif row.get("role") != want_wr:
            wrong_role_excluded += 1
    goal_from_scratch = scratch_same_kind_goal_cells(
        scratch_transport_cells, cells=cells, want_wr=want_wr
    )
    psr["scratch_transport_input_count"] = len(scratch_transport_cells)
    psr["scratch_goal_count"] = len(goal_from_scratch)
    psr["scratch_goal_without_map_row_count"] = without_map
    psr["scratch_goal_wrong_role_excluded_count"] = wrong_role_excluded

    if nearest_same_kind_transport_hops is None:
        psr["attempted"] = False
        psr["rejected_reason"] = "nearest_hops_none"
        return StubRouteRecoveryResult(
            accepted=False,
            trace=base_trace,
            new_transport_coords=frozenset(),
            chosen_r=None,
            stub_cell=None,
        )
    if nearest_same_kind_transport_hops > MAX_PASS12_STUB_ROUTE_RECOVERY_NEAREST_HOPS:
        psr["attempted"] = False
        psr["rejected_reason"] = "nearest_hops_over_cap"
        return StubRouteRecoveryResult(
            accepted=False,
            trace=base_trace,
            new_transport_coords=frozenset(),
            chosen_r=None,
            stub_cell=None,
        )

    blocked_body = frozenset(scratch_blocked_cells | {miner} | set(extensions))
    existing_same_kind = existing_same_kind_transport_cells_from_map(cells, want_wr=want_wr)
    goals = goal_transport_cells(
        cells=cells,
        want_wr=want_wr,
        scratch_transport_cells=scratch_transport_cells,
    )
    psr["goal_transport_cell_count"] = len(goals)
    psr["existing_same_kind_transport_cell_count"] = len(existing_same_kind)

    order = _rotation_order(row_r_raw)
    psr["candidate_rotation_count"] = len(order)
    saw_ok_stub = False
    saw_bfs_no_route = False
    saw_visit_cap = False
    saw_route_len = False
    saw_new_transport_over = False
    saw_extension_carve = False
    saw_stub_other = False
    stub_route_probe_last: dict[str, Any] | None = None
    rotation_candidates: list[tuple[tuple[int, int, int], int, Coord]] = []
    for cand_r in order:
        stub = shape_miner_output_cell(miner, cand_r)
        if stub is None:
            continue
        ok_space, rej = _stub_space_mvp(
            stub,
            cells=cells,
            mineable=mineable,
            blocked_body=blocked_body,
            want_wr=want_wr,
        )
        if not ok_space:
            if rej == "extension_carve_disabled":
                saw_extension_carve = True
            else:
                saw_stub_other = True
            continue
        pri = _stub_cell_recovery_priority(stub, cells)
        rotation_candidates.append((pri, cand_r, stub))
    rotation_candidates.sort(key=lambda t: (t[0][0], t[0][1], t[0][2], t[1]))
    for _pri, cand_r, stub in rotation_candidates:
        saw_ok_stub = True
        path, diag = _bfs_shortest_path(
            stub,
            goal_transport_cells=goals,
            cells=cells,
            mineable=mineable,
            blocked_body=blocked_body,
            want_wr=want_wr,
            max_edges=MAX_PASS12_STUB_ROUTE_RECOVERY_PATH_LEN,
        )
        if path is None:
            if diag.get("failure") == "visit_cap":
                saw_visit_cap = True
            else:
                saw_bfs_no_route = True
            relaxed_goals = _reachable_goals_under_edge_cap(
                stub,
                goal_transport_cells=goals,
                cells=cells,
                mineable=mineable,
                blocked_body=blocked_body,
                want_wr=want_wr,
                max_edges=512,
                max_visits=50_000,
            )
            stub_route_probe_last = {
                "stub_start_cell": [int(stub[0]), int(stub[1])],
                "cand_r": cand_r,
                "bfs_failure": diag.get("failure"),
                "expanded_nodes": diag.get("expanded_nodes"),
                "blocked_frontier_reason_counts": diag.get("blocked_frontier_reason_counts"),
                "last_frontier_sample": diag.get("last_frontier_sample"),
                "reachable_same_kind_goals_under_edge_cap_512": relaxed_goals,
                "local_neighbor_cells_around_stub": _local_neighbor_cells_around_stub(stub, cells),
            }
            continue
        route_len_edges = len(path) - 1
        if route_len_edges > MAX_PASS12_STUB_ROUTE_RECOVERY_PATH_LEN:
            saw_route_len = True
            psr["path_cell_count"] = len(path)
            psr["route_len_edges"] = route_len_edges
            continue
        path_cells = frozenset(path)
        new_t = path_cells - existing_same_kind - scratch_transport_cells
        if len(new_t) > MAX_PASS12_STUB_ROUTE_RECOVERY_NEW_TRANSPORT_CELLS:
            saw_new_transport_over = True
            psr["path_cell_count"] = len(path)
            psr["route_len_edges"] = route_len_edges
            psr["new_transport_cell_count"] = len(new_t)
            continue

        psr["accepted"] = True
        psr["rejected_reason"] = None
        psr["selected_r"] = cand_r
        psr["selected_stub_cell"] = [int(stub[0]), int(stub[1])]
        psr["path_cell_count"] = diag.get("path_cell_count")
        psr["route_len_edges"] = diag.get("route_len_edges")
        psr["path_cells"] = [
            [int(c[0]), int(c[1])] for c in sorted(path, key=lambda p: (p[1], p[0]))
        ]
        psr["new_transport_cell_count"] = len(new_t)
        psr["stub_route_probe_last"] = {
            "stub_start_cell": [int(stub[0]), int(stub[1])],
            "cand_r": cand_r,
            "bfs_failure": diag.get("failure"),
            "expanded_nodes": diag.get("expanded_nodes"),
            "blocked_frontier_reason_counts": diag.get("blocked_frontier_reason_counts"),
            "last_frontier_sample": diag.get("last_frontier_sample"),
            "reachable_same_kind_goals_under_edge_cap_512": _reachable_goals_under_edge_cap(
                stub,
                goal_transport_cells=goals,
                cells=cells,
                mineable=mineable,
                blocked_body=blocked_body,
                want_wr=want_wr,
                max_edges=512,
                max_visits=50_000,
            ),
            "local_neighbor_cells_around_stub": _local_neighbor_cells_around_stub(stub, cells),
        }
        return StubRouteRecoveryResult(
            accepted=True,
            trace=base_trace,
            new_transport_coords=new_t,
            chosen_r=cand_r,
            stub_cell=stub,
        )

    if stub_route_probe_last is not None:
        psr["stub_route_probe_last"] = stub_route_probe_last

    if saw_visit_cap:
        psr["rejected_reason"] = "visit_cap"
    elif saw_bfs_no_route:
        psr["rejected_reason"] = "no_same_kind_route"
    elif saw_route_len:
        psr["rejected_reason"] = "route_len_over_cap"
    elif saw_new_transport_over:
        psr["rejected_reason"] = "new_transport_cells_over_cap"
    elif not saw_ok_stub and saw_extension_carve:
        psr["rejected_reason"] = "extension_carve_disabled"
    elif saw_stub_other or saw_extension_carve:
        psr["rejected_reason"] = "no_stub_space"
    else:
        psr["rejected_reason"] = "no_same_kind_route"
    return StubRouteRecoveryResult(
        accepted=False,
        trace=base_trace,
        new_transport_coords=frozenset(),
        chosen_r=None,
        stub_cell=None,
    )
