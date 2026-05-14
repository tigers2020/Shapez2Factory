"""Pass12 merged-seed: NEAR_TRANSPORT missing-stub route recovery (pure probe).

``try_preserve_stub_route_recovery`` does **not** mutate ``Pass12LayoutScratch``; callers
commit ``new_transport_coords`` on success only.

Production NDJSON often shows ``bounded_recovery.tier_c_success_count == 0`` while
``occupied_neighbor_ring`` dominates because Tier B removes only the first 1-cell carve slot
and Tier C pairs require **cardinal** same-bundle extension neighbors; diagonal-only
extension clusters yield ``tier_c_skipped_no_candidate_pairs``. **Tier D**
(``bounded_output_reorientation_repack``) may repack extensions with
``foundation.extension_topology`` (4-neighbor only) after A/B/C fail. Roll up
``preserve_missing_stub_summary.bounded_recovery`` from per-drop ``preserve_stub_recovery``
tier_* fields (never read NDJSON back into the solver).
"""

from __future__ import annotations

import copy
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any, Literal

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import (
    output_offset_r,
    shape_miner_output_cell,
)
from django_apps.shapez_asteroid.extraction.shapez_grid import (
    is_legal_xy,
    neighbors4,
    step_cardinal,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation import (
    extension_topology as _ext_topo,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    COMMIT_REASON_DEGRADED_CONNECTED_RECOVERY,
    MAX_PASS12_STUB_ROUTE_RECOVERY_NEAREST_HOPS,
    MAX_PASS12_STUB_ROUTE_RECOVERY_NEW_TRANSPORT_CELLS,
    MAX_PASS12_STUB_ROUTE_RECOVERY_PATH_LEN,
    PASS12_MAX_EXTENSION_TILES,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTENSIONS,
    EXTRACTORS_FLUID,
    EXTRACTORS_SHAPE,
    layout_kind,
    want_role,
)

MAX_PASS12_TIER_C_PAIR_ATTEMPTS = 8


def _failure_reason_from_probe_dict(probe: Mapping[str, Any] | None) -> str | None:
    if not isinstance(probe, dict):
        return None
    pr = probe.get("post_bfs_rejection")
    if isinstance(pr, str) and pr:
        return pr
    bf = probe.get("bfs_failure")
    if isinstance(bf, str) and bf and bf != "no_bfs_attempt":
        return str(bf)
    return None


def _tier_failed_label(prefix: str, probe: Mapping[str, Any] | None) -> str | None:
    raw = _failure_reason_from_probe_dict(probe)
    if raw is None:
        return None
    return f"{prefix}_failed_{raw}"


def _stamp_psr_tier_success(
    psr: dict[str, Any],
    winner: Literal["A", "B", "C"],
    *,
    tier_a_nonempty: bool,
    tier_b_loop_ran: bool,
    tier_c_loop_ran: bool,
) -> None:
    psr["tier_a_attempted"] = tier_a_nonempty
    psr["tier_a_success"] = winner == "A"
    psr["tier_b_attempted"] = tier_b_loop_ran
    psr["tier_b_success"] = winner == "B"
    psr["tier_c_attempted"] = tier_c_loop_ran or winner == "C"
    psr["tier_c_success"] = winner == "C"
    if winner == "A":
        psr["tier_b_skip_reason"] = "skipped_after_tier_a_success"
        psr["tier_c_skip_reason"] = "skipped_after_tier_a_success"
    elif winner == "B":
        psr["tier_b_skip_reason"] = None
        psr["tier_c_skip_reason"] = "skipped_after_tier_b_success"
    else:
        psr["tier_b_skip_reason"] = None
        psr["tier_c_skip_reason"] = None


def _apply_failure_tier_trace(
    psr: dict[str, Any],
    *,
    tier_a: list[tuple[tuple[int, int, int], int, Coord]],
    tier_a_last_probe: dict[str, Any] | None,
    tier_b_list: list[Any],
    tier_b_loop_ran: bool,
    tier_b_last_fail: str | None,
    cells_carve_probe: dict[Coord, dict[str, Any]] | None,
    tier_c_loop_ran: bool,
    tier_c_last_fail: str | None,
) -> None:
    """Populate per-tier trace fields on rejected ``preserve_stub_recovery`` (NDJSON contract)."""

    psr["tier_a_attempted"] = bool(tier_a)
    psr["tier_a_success"] = False
    if tier_a:
        lp_a = tier_a_last_probe if isinstance(tier_a_last_probe, dict) else None
        if lp_a is None:
            spl = psr.get("stub_route_probe_last")
            lp_a = spl if isinstance(spl, dict) else None
        psr["tier_a_failure_reason"] = _tier_failed_label("tier_a", lp_a)
    psr["tier_b_attempted"] = tier_b_loop_ran
    psr["tier_b_success"] = False
    if not tier_b_list:
        psr["tier_b_skip_reason"] = (
            "tier_b_skipped_no_one_cell_carve_probe"
            if cells_carve_probe is None
            else "tier_b_skipped_no_tier_b_candidate_row"
        )
    elif tier_b_loop_ran:
        psr["tier_b_failure_reason"] = tier_b_last_fail
    psr["tier_c_success"] = False
    psr["tier_c_attempted"] = tier_c_loop_ran or ("C" in (psr.get("recovery_tier_attempted") or []))
    if tier_c_loop_ran:
        psr["tier_c_failure_reason"] = tier_c_last_fail
    elif "C" in (psr.get("recovery_tier_attempted") or []) and not tier_c_loop_ran:
        psr["tier_c_failure_reason"] = "tier_c_failed_stub_space_after_two_cell_pop"


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
    carved_extension_cells: frozenset[Coord] = field(default_factory=frozenset)
    tier_d_extensions_removed: frozenset[Coord] = field(default_factory=frozenset)
    tier_d_extension_placements: tuple[tuple[Coord, dict[str, Any]], ...] = field(
        default_factory=tuple
    )
    tier_d_final_extension_cells: frozenset[Coord] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.accepted:
            return
        psr = self.trace.get("preserve_stub_recovery")
        if isinstance(psr, dict):
            psr.pop("commit_reason", None)


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


def _goal_sample_list(goals: frozenset[Coord], *, limit: int = 8) -> list[list[int]]:
    """Deterministic bounded sample of goal coords for NDJSON contracts."""

    sorted_goals = sorted(goals, key=lambda p: (p[1], p[0]))
    return [[int(c[0]), int(c[1])] for c in sorted_goals[:limit]]


def _augment_stub_route_probe(
    stub: Coord,
    cand_r: int,
    goals: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    diag: dict[str, Any],
    *,
    mineable: frozenset[Coord],
    blocked_body: frozenset[Coord],
    want_wr: str,
    relaxed_goals: int | None = None,
    post_bfs_rejection: str | None = None,
    path_for_metrics: list[Coord] | None = None,
    new_transport_cell_count: int | None = None,
) -> dict[str, Any]:
    """Canonical ``stub_route_probe_last`` + fields mirrored on ``preserve_stub_recovery``."""

    if relaxed_goals is None:
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
    sc = [int(stub[0]), int(stub[1])]
    out: dict[str, Any] = {
        "start_cell": sc,
        "stub_start_cell": sc,
        "start": sc,
        "cand_r": cand_r,
        "goal_count": len(goals),
        "goal_sample": _goal_sample_list(goals, limit=8),
        "edge_cap": MAX_PASS12_STUB_ROUTE_RECOVERY_PATH_LEN,
        "max_new_transport_cells": MAX_PASS12_STUB_ROUTE_RECOVERY_NEW_TRANSPORT_CELLS,
        "bfs_failure": diag.get("failure"),
        "expanded_nodes": diag.get("expanded_nodes"),
        "blocked_frontier_reason_counts": diag.get("blocked_frontier_reason_counts"),
        "last_frontier_sample": diag.get("last_frontier_sample"),
        "reachable_same_kind_goals_under_edge_cap_512": relaxed_goals,
        "local_neighbor_cells_around_stub": _local_neighbor_cells_around_stub(stub, cells),
    }
    if post_bfs_rejection is not None:
        out["post_bfs_rejection"] = post_bfs_rejection
    if path_for_metrics is not None:
        out["path_cell_count"] = len(path_for_metrics)
        out["route_len_edges"] = len(path_for_metrics) - 1
    if new_transport_cell_count is not None:
        out["new_transport_cell_count"] = new_transport_cell_count
    return out


def _sentinel_probe_no_bfs(
    miner: Coord,
    goals: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
) -> dict[str, Any]:
    """When no rotation reached BFS: explicit contract for NDJSON consumers."""

    return {
        "start_cell": None,
        "stub_start_cell": None,
        "start": None,
        "cand_r": None,
        "goal_count": len(goals),
        "goal_sample": _goal_sample_list(goals, limit=8),
        "edge_cap": MAX_PASS12_STUB_ROUTE_RECOVERY_PATH_LEN,
        "max_new_transport_cells": MAX_PASS12_STUB_ROUTE_RECOVERY_NEW_TRANSPORT_CELLS,
        "bfs_failure": "no_bfs_attempt",
        "expanded_nodes": 0,
        "blocked_frontier_reason_counts": {},
        "last_frontier_sample": [],
        "reachable_same_kind_goals_under_edge_cap_512": 0,
        "local_neighbor_cells_around_stub": _local_neighbor_cells_around_stub(miner, cells),
    }


def _mirror_probe_contract_into_psr(psr: dict[str, Any], probe: dict[str, Any]) -> None:
    """Duplicate key probe scalars at ``preserve_stub_recovery`` root for flat NDJSON reads."""

    psr["stub_route_probe_last"] = probe
    psr["start_cell"] = probe.get("start_cell")
    psr["goal_count"] = probe.get("goal_count")
    psr["goal_sample"] = probe.get("goal_sample")
    psr["edge_cap"] = probe.get("edge_cap")
    psr["max_new_transport_cells"] = probe.get("max_new_transport_cells")
    psr["local_neighbor_cells_around_stub"] = probe.get("local_neighbor_cells_around_stub")


def _no_same_kind_route_subtype(
    *,
    blocked: Mapping[str, Any] | None,
    reachable_relaxed: int,
) -> str:
    """Tie-break: wrong_kind > edge_cap+goals > blocked_body > occupied; default edge or sealed."""

    b: dict[str, int] = {}
    if isinstance(blocked, dict):
        for k, v in blocked.items():
            if isinstance(v, int) and v > 0:
                b[str(k)] = v
    wk = b.get("wrong_kind_transport", 0)
    ee = b.get("exceeds_max_edges_cap", 0)
    bb = b.get("blocked_body", 0)
    oc = b.get("occupied_not_traversable", 0)
    mx = max(wk, ee, bb, oc, 0)
    if wk > 0 and wk == mx:
        return "wrong_kind_transport_near_stub"
    if ee == mx and mx > 0 and reachable_relaxed >= 1:
        return "same_kind_goal_unreachable_under_edge_cap"
    if bb == mx and mx > 0:
        return "stub_local_geometry_sealed"
    if oc == mx and mx > 0:
        return "occupied_neighbor_ring"
    if reachable_relaxed >= 1:
        return "same_kind_goal_unreachable_under_edge_cap"
    return "stub_local_geometry_sealed"


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


def _extension_bundle_component_ids(
    extensions: frozenset[Coord], cells: dict[Coord, dict[str, Any]]
) -> dict[Coord, int]:
    """4-neighbor components over ``extensions`` cells that are EXTENSIONS bodies."""

    valid = {c for c in extensions if (layout_kind(cells.get(c) or {}) or "") in EXTENSIONS}
    comp: dict[Coord, int] = {}
    next_id = 0
    for start in sorted(valid, key=lambda p: (p[1], p[0])):
        if start in comp:
            continue
        q: deque[Coord] = deque([start])
        comp[start] = next_id
        while q:
            c = q.popleft()
            x, y = c
            for nxt in neighbors4(x, y):
                if nxt not in valid or nxt in comp:
                    continue
                comp[nxt] = next_id
                q.append(nxt)
        next_id += 1
    return comp


def _neighbors_diagonal4(x: int, y: int) -> tuple[Coord, ...]:
    """Diagonal-only neighbors (not cardinal); skips illegal ``x == 0`` cells."""

    out: list[Coord] = []
    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        nx, ny = x + dx, y + dy
        if is_legal_xy(nx, ny):
            out.append((nx, ny))
    return tuple(out)


def _coord_key_blocker(c: Coord) -> str:
    return f"[{int(c[0])},{int(c[1])}]"


def _tier_c_cardinal_pairs_and_telemetry(
    *,
    miner: Coord,
    extensions: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    rotation_order: list[int],
) -> tuple[list[tuple[int, Coord, Coord]], dict[str, Any]]:
    """Cardinal-only same-bundle pairs plus Tier C NDJSON telemetry (no diagonal pairs)."""

    bundle = _extension_bundle_component_ids(extensions, cells)
    comp_sizes: dict[int, int] = {}
    for _c, comp_id in bundle.items():
        comp_sizes[comp_id] = comp_sizes.get(comp_id, 0) + 1

    direct_blockers: set[Coord] = set()
    seen: set[tuple[int, Coord, Coord]] = set()
    out: list[tuple[int, Coord, Coord]] = []
    partner_cells: set[Coord] = set()

    def _is_ext_body(c: Coord) -> bool:
        row = cells.get(c)
        return row is not None and (layout_kind(row) or "") in EXTENSIONS

    for cand_r in rotation_order:
        stub = shape_miner_output_cell(miner, cand_r)
        if stub is None or stub not in extensions:
            continue
        if not _is_ext_body(stub):
            continue
        stub_cid = bundle.get(stub)
        if stub_cid is None:
            continue
        direct_blockers.add(stub)
        sx, sy = stub
        for nxt in sorted(neighbors4(sx, sy), key=lambda p: (p[1], p[0])):
            if nxt not in extensions or not _is_ext_body(nxt):
                continue
            if bundle.get(nxt) != stub_cid:
                continue
            partner_cells.add(nxt)
            a, b = (stub, nxt) if stub <= nxt else (nxt, stub)
            key = (cand_r, a, b)
            if key in seen:
                continue
            seen.add(key)
            out.append((cand_r, a, b))

    blockers_sorted = sorted(direct_blockers, key=lambda p: (p[1], p[0]))
    ext_component_size_by_blocker: dict[str, int] = {}
    cardinal_neighbor_extension_count_by_blocker: dict[str, int] = {}
    same_bundle_cardinal_neighbor_count_by_blocker: dict[str, int] = {}

    for b in blockers_sorted:
        k = _coord_key_blocker(b)
        block_cid = bundle.get(b)
        ext_component_size_by_blocker[k] = (
            int(comp_sizes.get(block_cid, 0)) if block_cid is not None else 0
        )
        bx, by = b
        card_ext = 0
        same_card = 0
        for nxt in neighbors4(bx, by):
            if nxt not in extensions or not _is_ext_body(nxt):
                continue
            card_ext += 1
            if block_cid is not None and bundle.get(nxt) == block_cid:
                same_card += 1
        cardinal_neighbor_extension_count_by_blocker[k] = card_ext
        same_bundle_cardinal_neighbor_count_by_blocker[k] = same_card

    pair_sample: list[list[list[int]]] = [
        [[int(a[0]), int(a[1])], [int(b[0]), int(b[1])]]
        for _r, a, b in out[:MAX_PASS12_TIER_C_PAIR_ATTEMPTS]
    ]

    no_pair: dict[str, Any] | None = None
    if not out and blockers_sorted:
        all_no_cardinal_sb = all(
            same_bundle_cardinal_neighbor_count_by_blocker[_coord_key_blocker(b)] == 0
            for b in blockers_sorted
        )
        any_diag_ext = False
        for b in blockers_sorted:
            bx, by = b
            for nxt in _neighbors_diagonal4(bx, by):
                if nxt in extensions and _is_ext_body(nxt):
                    any_diag_ext = True
                    break
            if any_diag_ext:
                break
        blocker_has_only_diagonal_neighbors = bool(all_no_cardinal_sb and any_diag_ext)
        no_pair = {
            "stub_blocker_count": len(blockers_sorted),
            "extension_component_size_by_blocker": dict(
                sorted(ext_component_size_by_blocker.items(), key=lambda kv: kv[0])
            ),
            "cardinal_neighbor_extension_count_by_blocker": dict(
                sorted(cardinal_neighbor_extension_count_by_blocker.items(), key=lambda kv: kv[0])
            ),
            "same_bundle_cardinal_neighbor_count_by_blocker": dict(
                sorted(same_bundle_cardinal_neighbor_count_by_blocker.items(), key=lambda kv: kv[0])
            ),
            "blocker_has_only_diagonal_neighbors": blocker_has_only_diagonal_neighbors,
        }

    telemetry: dict[str, Any] = {
        "tier_c_direct_stub_blocker_cells": [[int(c[0]), int(c[1])] for c in blockers_sorted],
        "tier_c_same_bundle_cardinal_neighbor_cells": [
            [int(c[0]), int(c[1])] for c in sorted(partner_cells, key=lambda p: (p[1], p[0]))
        ],
        "tier_c_candidate_pair_count": len(out),
        "tier_c_candidate_pair_sample": pair_sample,
        "tier_c_pair_generation_mode": "cardinal_same_bundle_only",
        "tier_c_no_pair_diagnostic": no_pair,
    }
    return out, telemetry


def _maybe_success_from_bfs_path(
    *,
    stub: Coord,
    cand_r: int,
    path: list[Coord],
    diag: dict[str, Any],
    probe_cells: dict[Coord, dict[str, Any]],
    goals_work: frozenset[Coord],
    existing_work: frozenset[Coord],
    scratch_transport_cells: frozenset[Coord],
    blocked_body: frozenset[Coord],
    mineable: frozenset[Coord],
    want_wr: str,
    psr: dict[str, Any],
    base_trace: dict[str, Any],
    carved_coords: frozenset[Coord],
    use_carved: bool,
) -> StubRouteRecoveryResult | None:
    """Return success result or None when caps reject."""

    route_len_edges = len(path) - 1
    if route_len_edges > MAX_PASS12_STUB_ROUTE_RECOVERY_PATH_LEN:
        return None
    path_cells = frozenset(path)
    new_t = path_cells - existing_work - scratch_transport_cells
    if len(new_t) > MAX_PASS12_STUB_ROUTE_RECOVERY_NEW_TRANSPORT_CELLS:
        return None

    psr["accepted"] = True
    psr["rejected_reason"] = None
    psr["rejected_reason_subtype"] = None
    psr["commit_reason"] = COMMIT_REASON_DEGRADED_CONNECTED_RECOVERY
    psr["selected_r"] = cand_r
    psr["selected_stub_cell"] = [int(stub[0]), int(stub[1])]
    psr["path_cell_count"] = diag.get("path_cell_count")
    psr["route_len_edges"] = diag.get("route_len_edges")
    psr["path_cells"] = [[int(c[0]), int(c[1])] for c in sorted(path, key=lambda p: (p[1], p[0]))]
    psr["new_transport_cell_count"] = len(new_t)
    if use_carved:
        psr["extension_carve_applied"] = True
        if len(carved_coords) == 1:
            sc = next(iter(carved_coords))
            psr["carved_extension_cell"] = [int(sc[0]), int(sc[1])]
        else:
            smin = sorted(carved_coords, key=lambda p: (p[1], p[0]))[0]
            psr["carved_extension_cell"] = [int(smin[0]), int(smin[1])]
    stub_ok_probe = _augment_stub_route_probe(
        stub,
        cand_r,
        goals_work,
        probe_cells,
        diag,
        mineable=mineable,
        blocked_body=blocked_body,
        want_wr=want_wr,
        path_for_metrics=path,
    )
    _mirror_probe_contract_into_psr(psr, stub_ok_probe)
    return StubRouteRecoveryResult(
        accepted=True,
        trace=base_trace,
        new_transport_coords=new_t,
        chosen_r=cand_r,
        stub_cell=stub,
        carved_extension_cells=carved_coords,
    )


def _probe_stub_route_once(
    *,
    stub: Coord,
    cand_r: int,
    probe_cells: dict[Coord, dict[str, Any]],
    use_carved: bool,
    carved_coords: frozenset[Coord],
    goals: frozenset[Coord],
    existing_same_kind: frozenset[Coord],
    scratch_transport_cells: frozenset[Coord],
    blocked_body: frozenset[Coord],
    mineable: frozenset[Coord],
    want_wr: str,
    psr: dict[str, Any],
    base_trace: dict[str, Any],
    saw_visit_cap: list[bool],
    saw_bfs_no_route: list[bool],
    saw_route_len: list[bool],
    saw_new_transport_over: list[bool],
    post_carve_no_route: list[bool],
) -> StubRouteRecoveryResult | None:
    """One stub+rotation BFS attempt; updates ``saw_*`` flags and ``stub_route_probe_last``."""

    blocked_probe = frozenset(blocked_body - carved_coords) if carved_coords else blocked_body
    goals_work = (
        goal_transport_cells(
            cells=probe_cells,
            want_wr=want_wr,
            scratch_transport_cells=scratch_transport_cells,
        )
        if use_carved
        else goals
    )
    existing_work = (
        existing_same_kind_transport_cells_from_map(probe_cells, want_wr=want_wr)
        if use_carved
        else existing_same_kind
    )
    path, diag = _bfs_shortest_path(
        stub,
        goal_transport_cells=goals_work,
        cells=probe_cells,
        mineable=mineable,
        blocked_body=blocked_probe,
        want_wr=want_wr,
        max_edges=MAX_PASS12_STUB_ROUTE_RECOVERY_PATH_LEN,
    )
    if path is None:
        if diag.get("failure") == "visit_cap":
            saw_visit_cap[0] = True
        else:
            saw_bfs_no_route[0] = True
        if use_carved:
            post_carve_no_route[0] = True
            psr["post_carve_rejected_reason"] = "no_same_kind_route"
        relaxed_goals = _reachable_goals_under_edge_cap(
            stub,
            goal_transport_cells=goals_work,
            cells=probe_cells,
            mineable=mineable,
            blocked_body=blocked_probe,
            want_wr=want_wr,
            max_edges=512,
            max_visits=50_000,
        )
        stub_route_probe_last = _augment_stub_route_probe(
            stub,
            cand_r,
            goals_work,
            probe_cells,
            diag,
            mineable=mineable,
            blocked_body=blocked_probe,
            want_wr=want_wr,
            relaxed_goals=relaxed_goals,
        )
        _mirror_probe_contract_into_psr(psr, stub_route_probe_last)
        return None
    route_len_edges = len(path) - 1
    if route_len_edges > MAX_PASS12_STUB_ROUTE_RECOVERY_PATH_LEN:
        saw_route_len[0] = True
        psr["path_cell_count"] = len(path)
        psr["route_len_edges"] = route_len_edges
        stub_route_probe_last = _augment_stub_route_probe(
            stub,
            cand_r,
            goals_work,
            probe_cells,
            diag,
            mineable=mineable,
            blocked_body=blocked_probe,
            want_wr=want_wr,
            post_bfs_rejection="route_len_over_cap",
            path_for_metrics=path,
        )
        _mirror_probe_contract_into_psr(psr, stub_route_probe_last)
        return None
    path_cells = frozenset(path)
    new_t = path_cells - existing_work - scratch_transport_cells
    if len(new_t) > MAX_PASS12_STUB_ROUTE_RECOVERY_NEW_TRANSPORT_CELLS:
        saw_new_transport_over[0] = True
        psr["path_cell_count"] = len(path)
        psr["route_len_edges"] = route_len_edges
        psr["new_transport_cell_count"] = len(new_t)
        stub_route_probe_last = _augment_stub_route_probe(
            stub,
            cand_r,
            goals_work,
            probe_cells,
            diag,
            mineable=mineable,
            blocked_body=blocked_probe,
            want_wr=want_wr,
            post_bfs_rejection="new_transport_cells_over_cap",
            path_for_metrics=path,
            new_transport_cell_count=len(new_t),
        )
        _mirror_probe_contract_into_psr(psr, stub_route_probe_last)
        return None
    return _maybe_success_from_bfs_path(
        stub=stub,
        cand_r=cand_r,
        path=path,
        diag=diag,
        probe_cells=probe_cells,
        goals_work=goals_work,
        existing_work=existing_work,
        scratch_transport_cells=scratch_transport_cells,
        blocked_body=blocked_probe,
        mineable=mineable,
        want_wr=want_wr,
        psr=psr,
        base_trace=base_trace,
        carved_coords=carved_coords,
        use_carved=use_carved,
    )


MAX_PASS12_TIER_D_TOPOLOGY_ATTEMPTS = 48

# NDJSON / ``preserve_stub_recovery`` contract when ``tier_d_success`` is true (plan 2026-05-13).
TIER_D_SUCCESS_TRACE_FIELD_KEYS: tuple[str, ...] = (
    "tier_d_attempted",
    "tier_d_success",
    "tier_d_skip_reason",
    "tier_d_failure_reason",
    "output_repack_candidate_count",
    "output_repack_candidate_sample",
    "output_repack_selected_rotation",
    "output_repack_removed_extension_cells",
    "output_repack_replaced_extension_cells",
    "output_repack_preserved_extension_count",
    "output_repack_route_len_edges",
)


def tier_d_success_preserve_stub_recovery_trace_contract_ok(psr: Mapping[str, Any]) -> bool:
    """True iff ``psr`` satisfies Tier D success telemetry keys and null-skip/failure fields."""

    if psr.get("tier_d_success") is not True:
        return False
    for key in TIER_D_SUCCESS_TRACE_FIELD_KEYS:
        if key not in psr:
            return False
    if psr.get("tier_d_attempted") is not True:
        return False
    if psr.get("tier_d_skip_reason") is not None or psr.get("tier_d_failure_reason") is not None:
        return False
    occ = psr.get("output_repack_candidate_count")
    if not isinstance(occ, int) or occ < 1:
        return False
    if not isinstance(psr.get("output_repack_candidate_sample"), list):
        return False
    if not isinstance(psr.get("output_repack_selected_rotation"), int):
        return False
    rem = psr.get("output_repack_removed_extension_cells")
    rep = psr.get("output_repack_replaced_extension_cells")
    if not isinstance(rem, list) or len(rem) < 1:
        return False
    if not isinstance(rep, list) or len(rep) < 1:
        return False
    pec = psr.get("output_repack_preserved_extension_count")
    if not isinstance(pec, int) or pec < 1:
        return False
    rle = psr.get("output_repack_route_len_edges")
    if not isinstance(rle, int) or rle < 0:
        return False
    return True


def _tier_d_extensions_cardinally_connected(miner: Coord, extensions: frozenset[Coord]) -> bool:
    """True iff every extension cell is reachable from ``miner`` via 4-neighbor hops in-set."""

    if not extensions:
        return True
    seen_ext: set[Coord] = set()
    q: deque[Coord] = deque([miner])
    visited: set[Coord] = {miner}
    while q:
        c = q.popleft()
        x, y = c
        for nxt in neighbors4(x, y):
            if nxt not in extensions or nxt in visited:
                continue
            visited.add(nxt)
            seen_ext.add(nxt)
            q.append(nxt)
    return seen_ext == set(extensions)


def _tier_d_blocked_for_enumeration(
    cells: Mapping[Coord, dict[str, Any]],
    *,
    miner: Coord,
    extensions: frozenset[Coord],
    scratch_blocked: frozenset[Coord],
) -> frozenset[Coord]:
    """Cells that block extension repack enumeration (other buildings + scratch blocked)."""

    out: set[Coord] = set(scratch_blocked)
    for c, row in cells.items():
        if c == miner or c in extensions:
            continue
        if row.get("role") != "occupied":
            continue
        lk = layout_kind(row) or ""
        if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID or lk in EXTENSIONS:
            out.add(c)
    return frozenset(out)


def _tier_d_stub_skip_reason(
    stub: Coord | None,
    *,
    miner: Coord,
    extensions: frozenset[Coord],
    cells: Mapping[Coord, dict[str, Any]],
    scratch_blocked: frozenset[Coord],
    want_wr: str,
) -> str | None:
    """None when stub is usable for Tier D repack on this rotation (before strip)."""

    if stub is None:
        return "tier_d_stub_none"
    if stub in scratch_blocked:
        return "tier_d_stub_blocked_protected_corridor"
    if stub in extensions:
        return None
    row = cells.get(stub)
    if row is None:
        return None
    role = row.get("role")
    if role == "inferred":
        return None
    if role == want_wr:
        return "tier_d_stub_blocked_same_kind_transport"
    if role == ("belt" if want_wr == "pipe" else "pipe"):
        return "tier_d_stub_blocked_other_kind_transport"
    if role != "occupied":
        return "tier_d_stub_blocked_unsupported_role"
    lk = layout_kind(row) or ""
    if lk in EXTENSIONS:
        return "tier_d_stub_blocked_foreign_extension"
    if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
        ex = (int(row["x"]), int(row["y"]))
        if ex != miner:
            return "tier_d_stub_blocked_unrelated_extractor"
        return None
    if lk == "asteroid_field":
        return None
    return "tier_d_stub_blocked_occupied_not_void"


def _tier_d_extension_row_template(
    cells: Mapping[Coord, dict[str, Any]], extensions: frozenset[Coord]
) -> dict[str, Any]:
    for c in sorted(extensions, key=lambda p: (p[1], p[0])):
        row = cells.get(c)
        if row and (layout_kind(row) or "") in EXTENSIONS:
            return dict(row)
    return {"role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"}


def _try_tier_d_bounded_output_reorientation_repack(
    *,
    miner: Coord,
    extensions: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    scratch_transport_cells: frozenset[Coord],
    scratch_blocked_cells: frozenset[Coord],
    want_wr: str,
    goals: frozenset[Coord],
    existing_same_kind: frozenset[Coord],
    order: list[int],
    psr: dict[str, Any],
    base_trace: dict[str, Any],
    saw_visit_cap: list[bool],
    saw_bfs_no_route: list[bool],
    saw_route_len: list[bool],
    saw_new_transport_over: list[bool],
    post_carve_no_route: list[bool],
) -> StubRouteRecoveryResult | None:
    """Tier D: strip local extensions, enumerate cardinal repacks, re-probe stub route."""

    if not extensions:
        psr["tier_d_attempted"] = False
        psr["tier_d_skip_reason"] = "tier_d_skipped_empty_bundle"
        return None
    if not _tier_d_extensions_cardinally_connected(miner, extensions):
        psr["tier_d_attempted"] = False
        psr["tier_d_skip_reason"] = "tier_d_skipped_diagonal_only_extension_topology"
        return None

    cells_strip: dict[Coord, dict[str, Any]] = {c: dict(r) for c, r in cells.items()}
    for ec in extensions:
        cells_strip.pop(ec, None)

    transport_strip = frozenset(
        c for c, row in cells_strip.items() if row.get("role") in ("belt", "pipe")
    )
    blocked_enum = _tier_d_blocked_for_enumeration(
        cells, miner=miner, extensions=extensions, scratch_blocked=scratch_blocked_cells
    )
    tpl = _tier_d_extension_row_template(cells, extensions)
    ext_layout_kind = str(tpl.get("layout_kind") or "fluid_extension")
    surface = str(tpl.get("surface") or ("fluid" if "fluid" in ext_layout_kind else "shape"))

    candidate_count = 0
    sample: list[dict[str, Any]] = []
    last_fail: str | None = None
    any_rotation_reached_topo = False
    stop_all = False

    for cand_r in order:
        if stop_all:
            break
        stub = shape_miner_output_cell(miner, cand_r)
        sk = _tier_d_stub_skip_reason(
            stub,
            miner=miner,
            extensions=extensions,
            cells=cells,
            scratch_blocked=scratch_blocked_cells,
            want_wr=want_wr,
        )
        if sk is not None:
            continue
        assert stub is not None
        out_dir = output_offset_r(cand_r)
        topo_list = _ext_topo.enumerate_extension_topologies(
            miner,
            out_dir,
            mineable,
            blocked_enum,
            transport_strip,
            max_extensions=PASS12_MAX_EXTENSION_TILES,
        )
        for topo in topo_list:
            if topo.extension_count != len(extensions):
                continue
            any_rotation_reached_topo = True
            candidate_count += 1
            if len(sample) < 5:
                sample.append(
                    {
                        "cand_r": int(cand_r),
                        "extension_cells": [
                            [int(c[0]), int(c[1])]
                            for c in sorted(topo.extension_cells, key=lambda p: (p[1], p[0]))
                        ],
                    }
                )
            if candidate_count > MAX_PASS12_TIER_D_TOPOLOGY_ATTEMPTS:
                stop_all = True
                break
            cells_try = dict(cells_strip)
            placements: list[tuple[Coord, dict[str, Any]]] = []
            ok_place = True
            for cell, dx, dy in sorted(topo.facings, key=lambda t: (t[0][1], t[0][0], t[1], t[2])):
                parent = step_cardinal(cell[0], cell[1], dx, dy)
                if parent is None:
                    ok_place = False
                    break
                rf = _ext_topo.rotation_r_for_extension_facing_parent((dx, dy))
                erow = {
                    "x": cell[0],
                    "y": cell[1],
                    "role": "occupied",
                    "layout_kind": ext_layout_kind,
                    "surface": surface,
                    "r": rf,
                }
                cells_try[cell] = erow
                placements.append((cell, dict(erow)))
            if not ok_place:
                continue
            blocked_try = frozenset(scratch_blocked_cells | {miner} | topo.extension_cells)
            ok_res = _probe_stub_route_once(
                stub=stub,
                cand_r=cand_r,
                probe_cells=cells_try,
                use_carved=False,
                carved_coords=frozenset(),
                goals=goals,
                existing_same_kind=existing_same_kind,
                scratch_transport_cells=scratch_transport_cells,
                blocked_body=blocked_try,
                mineable=mineable,
                want_wr=want_wr,
                psr=psr,
                base_trace=base_trace,
                saw_visit_cap=saw_visit_cap,
                saw_bfs_no_route=saw_bfs_no_route,
                saw_route_len=saw_route_len,
                saw_new_transport_over=saw_new_transport_over,
                post_carve_no_route=post_carve_no_route,
            )
            if ok_res is None:
                lp = psr.get("stub_route_probe_last")
                last_fail = (
                    _tier_failed_label("tier_d", lp if isinstance(lp, dict) else None) or last_fail
                )
                continue
            psr["recovery_tier_attempted"].append("D")
            psr["tier_d_attempted"] = True
            psr["tier_d_success"] = True
            psr["tier_d_skip_reason"] = None
            psr["tier_d_failure_reason"] = None
            psr["output_repack_candidate_count"] = candidate_count
            psr["output_repack_candidate_sample"] = sample
            psr["output_repack_selected_rotation"] = int(cand_r)
            psr["output_repack_removed_extension_cells"] = [
                [int(c[0]), int(c[1])] for c in sorted(extensions, key=lambda p: (p[1], p[0]))
            ]
            psr["output_repack_replaced_extension_cells"] = [
                [int(c[0]), int(c[1])]
                for c, _ in sorted(placements, key=lambda t: (t[0][1], t[0][0]))
            ]
            psr["output_repack_preserved_extension_count"] = len(extensions)
            _rle = psr.get("route_len_edges")
            psr["output_repack_route_len_edges"] = int(_rle) if isinstance(_rle, int) else _rle
            return replace(
                ok_res,
                carved_extension_cells=frozenset(),
                tier_d_extensions_removed=extensions,
                tier_d_extension_placements=tuple((c, dict(r)) for c, r in placements),
                tier_d_final_extension_cells=topo.extension_cells,
            )
        if stop_all:
            break

    psr["recovery_tier_attempted"].append("D")
    psr["tier_d_attempted"] = True
    psr["tier_d_success"] = False
    psr["output_repack_candidate_count"] = candidate_count
    psr["output_repack_candidate_sample"] = sample
    if not any_rotation_reached_topo:
        psr["tier_d_skip_reason"] = "tier_d_skipped_no_repack_candidates"
        psr["tier_d_failure_reason"] = None
    else:
        psr["tier_d_skip_reason"] = None
        psr["tier_d_failure_reason"] = last_fail or "tier_d_failed_exhausted_candidates"
    return None


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
        "extension_carve_considered": False,
        "extension_carve_candidate_cells": [],
        "extension_carve_skip_reason": None,
        "extension_carve_attempted": False,
        "extension_carve_applied": None,
        "carved_extension_cell": None,
        "post_carve_rejected_reason": None,
        "recovery_tier_attempted": [],
        "output_reorientation_attempted": False,
        "output_reorientation_success": False,
        "bounded_bundle_rollback_attempted": False,
        "bounded_bundle_rollback_cells": [],
        "bounded_bundle_rollback_success": False,
        "tier_a_attempted": False,
        "tier_a_success": False,
        "tier_a_failure_reason": None,
        "tier_b_attempted": False,
        "tier_b_success": False,
        "tier_b_skip_reason": None,
        "tier_b_failure_reason": None,
        "tier_c_attempted": False,
        "tier_c_success": False,
        "tier_c_skip_reason": None,
        "tier_c_failure_reason": None,
        "tier_c_direct_stub_blocker_cells": [],
        "tier_c_same_bundle_cardinal_neighbor_cells": [],
        "tier_c_candidate_pair_count": 0,
        "tier_c_candidate_pair_sample": [],
        "tier_c_pair_generation_mode": None,
        "tier_c_no_pair_diagnostic": None,
        "tier_d_attempted": False,
        "tier_d_success": False,
        "tier_d_skip_reason": None,
        "tier_d_failure_reason": None,
        "output_repack_candidate_count": 0,
        "output_repack_candidate_sample": [],
        "output_repack_selected_rotation": None,
        "output_repack_removed_extension_cells": [],
        "output_repack_replaced_extension_cells": [],
        "output_repack_preserved_extension_count": None,
        "output_repack_route_len_edges": None,
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
    saw_ok_stub = [False]
    saw_visit_cap = [False]
    saw_bfs_no_route = [False]
    saw_route_len = [False]
    saw_new_transport_over = [False]
    saw_extension_carve = False
    saw_stub_other = False
    post_carve_no_route = [False]
    tier_a_last_probe: dict[str, Any] | None = None
    tier_a: list[tuple[tuple[int, int, int], int, Coord]] = []
    cells_carve_probe: dict[Coord, dict[str, Any]] | None = None
    carved_output_cell: Coord | None = None
    carved_cand_r: int | None = None
    tier_b_loop_ran = False
    tier_b_last_fail: str | None = None
    tier_c_loop_ran = False
    tier_c_last_fail: str | None = None
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
        if ok_space:
            pri = _stub_cell_recovery_priority(stub, cells)
            tier_a.append((pri, cand_r, stub))
            continue
        if rej == "extension_carve_disabled":
            saw_extension_carve = True
            psr["extension_carve_considered"] = True
            row_st = cells.get(stub)
            carved_ok = False
            if stub not in extensions:
                if psr["extension_carve_skip_reason"] is None:
                    psr["extension_carve_skip_reason"] = "stub_not_in_extensions_set"
            elif row_st is None:
                if psr["extension_carve_skip_reason"] is None:
                    psr["extension_carve_skip_reason"] = "no_row_at_stub_cell"
            elif (layout_kind(row_st) or "") not in EXTENSIONS:
                if psr["extension_carve_skip_reason"] is None:
                    psr["extension_carve_skip_reason"] = "stub_cell_not_extension_layout_kind"
            elif cells_carve_probe is not None:
                if psr["extension_carve_skip_reason"] is None:
                    psr["extension_carve_skip_reason"] = "extension_carve_slot_already_used"
            else:
                cells_try = dict(cells)
                cells_try.pop(stub, None)
                ok2, rej2 = _stub_space_mvp(
                    stub,
                    cells=cells_try,
                    mineable=mineable,
                    blocked_body=frozenset(blocked_body - {stub}),
                    want_wr=want_wr,
                )
                psr["extension_carve_attempted"] = True
                psr["extension_carve_candidate_cells"] = [[int(stub[0]), int(stub[1])]]
                if ok2:
                    cells_carve_probe = cells_try
                    carved_output_cell = stub
                    carved_cand_r = cand_r
                    carved_ok = True
                    psr["extension_carve_skip_reason"] = None
                    break
                if psr["extension_carve_skip_reason"] is None:
                    psr["extension_carve_skip_reason"] = (
                        f"carve_pop_still_blocks_stub_space:{rej2}"
                        if rej2
                        else "carve_pop_still_blocks_stub_space"
                    )
            if not carved_ok:
                saw_stub_other = True
        else:
            saw_stub_other = True

    if tier_a:
        psr["recovery_tier_attempted"].append("A")
        psr["output_reorientation_attempted"] = True
        tier_a.sort(key=lambda t: (t[0][0], t[0][1], t[0][2], t[1]))
        for _pri, cand_r, stub in tier_a:
            saw_ok_stub[0] = True
            ok_res = _probe_stub_route_once(
                stub=stub,
                cand_r=cand_r,
                probe_cells=cells,
                use_carved=False,
                carved_coords=frozenset(),
                goals=goals,
                existing_same_kind=existing_same_kind,
                scratch_transport_cells=scratch_transport_cells,
                blocked_body=blocked_body,
                mineable=mineable,
                want_wr=want_wr,
                psr=psr,
                base_trace=base_trace,
                saw_visit_cap=saw_visit_cap,
                saw_bfs_no_route=saw_bfs_no_route,
                saw_route_len=saw_route_len,
                saw_new_transport_over=saw_new_transport_over,
                post_carve_no_route=post_carve_no_route,
            )
            if ok_res is not None:
                psr["output_reorientation_success"] = True
                _stamp_psr_tier_success(
                    psr,
                    "A",
                    tier_a_nonempty=True,
                    tier_b_loop_ran=False,
                    tier_c_loop_ran=False,
                )
                return ok_res
        psr["output_reorientation_success"] = False
        lp = psr.get("stub_route_probe_last")
        if isinstance(lp, dict):
            tier_a_last_probe = copy.deepcopy(lp)

    tier_b_list: list[
        tuple[tuple[int, int, int], int, Coord, dict[Coord, dict[str, Any]], frozenset[Coord]]
    ] = []
    if (
        cells_carve_probe is not None
        and carved_output_cell is not None
        and carved_cand_r is not None
    ):
        pri_b = _stub_cell_recovery_priority(carved_output_cell, cells_carve_probe)
        tier_b_list.append(
            (
                pri_b,
                carved_cand_r,
                carved_output_cell,
                cells_carve_probe,
                frozenset({carved_output_cell}),
            )
        )
    if tier_b_list:
        psr["recovery_tier_attempted"].append("B")
        psr["bounded_bundle_rollback_attempted"] = True
        cc0 = tier_b_list[0][4]
        psr["bounded_bundle_rollback_cells"] = [[int(c[0]), int(c[1])] for c in sorted(cc0)]
        tier_b_list.sort(key=lambda t: (t[0][0], t[0][1], t[0][2], t[1]))
        for _pri, cand_r, stub, probe_cells, carved in tier_b_list:
            tier_b_loop_ran = True
            saw_ok_stub[0] = True
            ok_res = _probe_stub_route_once(
                stub=stub,
                cand_r=cand_r,
                probe_cells=probe_cells,
                use_carved=True,
                carved_coords=carved,
                goals=goals,
                existing_same_kind=existing_same_kind,
                scratch_transport_cells=scratch_transport_cells,
                blocked_body=blocked_body,
                mineable=mineable,
                want_wr=want_wr,
                psr=psr,
                base_trace=base_trace,
                saw_visit_cap=saw_visit_cap,
                saw_bfs_no_route=saw_bfs_no_route,
                saw_route_len=saw_route_len,
                saw_new_transport_over=saw_new_transport_over,
                post_carve_no_route=post_carve_no_route,
            )
            if ok_res is not None:
                psr["bounded_bundle_rollback_success"] = True
                _stamp_psr_tier_success(
                    psr,
                    "B",
                    tier_a_nonempty=bool(tier_a),
                    tier_b_loop_ran=True,
                    tier_c_loop_ran=False,
                )
                return ok_res
            lp_b = psr.get("stub_route_probe_last")
            tb = _tier_failed_label("tier_b", lp_b if isinstance(lp_b, dict) else None)
            tier_b_last_fail = tb or tier_b_last_fail

    tier_c_specs, tier_c_telemetry = _tier_c_cardinal_pairs_and_telemetry(
        miner=miner,
        extensions=extensions,
        cells=cells,
        rotation_order=order,
    )
    psr.update(tier_c_telemetry)
    if cells_carve_probe is None:
        psr["tier_c_skip_reason"] = "tier_c_skipped_no_one_cell_carve_probe_map"
        tier_c_specs = []
        psr["tier_c_no_pair_diagnostic"] = None
    elif not tier_c_specs:
        psr["tier_c_skip_reason"] = "tier_c_skipped_no_candidate_pairs"
    if tier_c_specs:
        psr["recovery_tier_attempted"].append("C")
        psr["bounded_bundle_rollback_attempted"] = True
    for cand_r, a, b in tier_c_specs[:MAX_PASS12_TIER_C_PAIR_ATTEMPTS]:
        cells_try = dict(cells)
        cells_try.pop(a, None)
        cells_try.pop(b, None)
        carved2 = frozenset({a, b})
        stub = shape_miner_output_cell(miner, cand_r)
        if stub is None:
            continue
        ok_space, _rej = _stub_space_mvp(
            stub,
            cells=cells_try,
            mineable=mineable,
            blocked_body=frozenset(blocked_body - carved2),
            want_wr=want_wr,
        )
        if not ok_space:
            continue
        psr["bounded_bundle_rollback_cells"] = [
            [int(a[0]), int(a[1])],
            [int(b[0]), int(b[1])],
        ]
        saw_ok_stub[0] = True
        tier_c_loop_ran = True
        ok_res = _probe_stub_route_once(
            stub=stub,
            cand_r=cand_r,
            probe_cells=cells_try,
            use_carved=True,
            carved_coords=carved2,
            goals=goals,
            existing_same_kind=existing_same_kind,
            scratch_transport_cells=scratch_transport_cells,
            blocked_body=blocked_body,
            mineable=mineable,
            want_wr=want_wr,
            psr=psr,
            base_trace=base_trace,
            saw_visit_cap=saw_visit_cap,
            saw_bfs_no_route=saw_bfs_no_route,
            saw_route_len=saw_route_len,
            saw_new_transport_over=saw_new_transport_over,
            post_carve_no_route=post_carve_no_route,
        )
        if ok_res is not None:
            psr["bounded_bundle_rollback_success"] = True
            _stamp_psr_tier_success(
                psr,
                "C",
                tier_a_nonempty=bool(tier_a),
                tier_b_loop_ran=tier_b_loop_ran,
                tier_c_loop_ran=True,
            )
            return ok_res
        lp_c = psr.get("stub_route_probe_last")
        tc = _tier_failed_label("tier_c", lp_c if isinstance(lp_c, dict) else None)
        tier_c_last_fail = tc or tier_c_last_fail

    d_res = _try_tier_d_bounded_output_reorientation_repack(
        miner=miner,
        extensions=extensions,
        cells=cells,
        mineable=mineable,
        scratch_transport_cells=scratch_transport_cells,
        scratch_blocked_cells=scratch_blocked_cells,
        want_wr=want_wr,
        goals=goals,
        existing_same_kind=existing_same_kind,
        order=order,
        psr=psr,
        base_trace=base_trace,
        saw_visit_cap=saw_visit_cap,
        saw_bfs_no_route=saw_bfs_no_route,
        saw_route_len=saw_route_len,
        saw_new_transport_over=saw_new_transport_over,
        post_carve_no_route=post_carve_no_route,
    )
    if d_res is not None:
        return d_res

    if tier_a_last_probe is not None:
        psr["stub_route_probe_last"] = tier_a_last_probe
        _mirror_probe_contract_into_psr(psr, tier_a_last_probe)

    _apply_failure_tier_trace(
        psr,
        tier_a=tier_a,
        tier_a_last_probe=tier_a_last_probe,
        tier_b_list=tier_b_list,
        tier_b_loop_ran=tier_b_loop_ran,
        tier_b_last_fail=tier_b_last_fail,
        cells_carve_probe=cells_carve_probe,
        tier_c_loop_ran=tier_c_loop_ran,
        tier_c_last_fail=tier_c_last_fail,
    )

    if (
        not tier_a
        and saw_extension_carve
        and not saw_visit_cap[0]
        and not saw_route_len[0]
        and not saw_new_transport_over[0]
    ):
        probe = _sentinel_probe_no_bfs(miner, goals, cells)
        psr["stub_route_probe_last"] = probe
        _mirror_probe_contract_into_psr(psr, probe)
        psr["rejected_reason"] = "extension_carve_disabled"
        psr["rejected_reason_subtype"] = None
        if psr["extension_carve_attempted"] and psr.get("extension_carve_applied") is None:
            psr["extension_carve_applied"] = False
        return StubRouteRecoveryResult(
            accepted=False,
            trace=base_trace,
            new_transport_coords=frozenset(),
            chosen_r=None,
            stub_cell=None,
        )

    stub_route_probe_last = psr.get("stub_route_probe_last")
    if stub_route_probe_last is None:
        stub_route_probe_last = _sentinel_probe_no_bfs(miner, goals, cells)
    _mirror_probe_contract_into_psr(psr, stub_route_probe_last)

    if saw_visit_cap[0]:
        psr["rejected_reason"] = "visit_cap"
        psr["rejected_reason_subtype"] = None
    elif saw_route_len[0]:
        psr["rejected_reason"] = "route_len_over_cap"
        psr["rejected_reason_subtype"] = None
    elif saw_new_transport_over[0]:
        psr["rejected_reason"] = "new_transport_cells_over_cap"
        psr["rejected_reason_subtype"] = None
    elif saw_bfs_no_route[0]:
        psr["rejected_reason"] = "no_same_kind_route"
        psr["rejected_reason_subtype"] = _no_same_kind_route_subtype(
            blocked=stub_route_probe_last.get("blocked_frontier_reason_counts"),
            reachable_relaxed=int(
                stub_route_probe_last.get("reachable_same_kind_goals_under_edge_cap_512") or 0
            ),
        )
    elif not saw_ok_stub[0] and saw_extension_carve:
        psr["rejected_reason"] = "extension_carve_disabled"
        psr["rejected_reason_subtype"] = None
    elif saw_stub_other or saw_extension_carve:
        psr["rejected_reason"] = "no_stub_space"
        psr["rejected_reason_subtype"] = None
    else:
        psr["rejected_reason"] = "no_same_kind_route"
        psr["rejected_reason_subtype"] = _no_same_kind_route_subtype(
            blocked=stub_route_probe_last.get("blocked_frontier_reason_counts"),
            reachable_relaxed=int(
                stub_route_probe_last.get("reachable_same_kind_goals_under_edge_cap_512") or 0
            ),
        )
    if psr["extension_carve_attempted"] and psr.get("extension_carve_applied") is None:
        psr["extension_carve_applied"] = False
    return StubRouteRecoveryResult(
        accepted=False,
        trace=base_trace,
        new_transport_coords=frozenset(),
        chosen_r=None,
        stub_cell=None,
    )
