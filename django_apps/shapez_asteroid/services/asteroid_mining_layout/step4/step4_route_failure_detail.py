"""STEP4 routing failure observability (goal/trunk/blocked/budget classification)."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_failure_category as _s4fc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_replay_overlay as _s4rov,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_routing_permission as _s4_perm,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_search_diagnostics as _s4sd,
)

_MAX_NEAREST_TRANSPORT_BFS_VISITS = 50_000
_MAX_REACHABLE_GOAL_BFS_VISITS = 50_000

# Canonical telemetry key order (JSON object insertion order for stable serialization).
ROUTING_FAILURE_DETAIL_KEYS: tuple[str, ...] = (
    "extractor_id",
    "placement_id",
    "transport_kind",
    "stub_cell",
    "placement_commit_state",
    "blocked_reason",
    "blocked_reason_near_stub",
    "nearest_blocked_cell",
    "nearest_blocked_zone",
    "existing_trunk_present",
    "trunk_seed_candidate_count",
    "route_goal_set_size",
    "reachable_goal_count",
    "reachable_existing_trunk_count",
    "reachable_exterior_margin_count",
    "candidate_expanded_nodes",
    "search_mode",
    "fallback_reason",
    "search_budget_exhausted",
    "replacement_search_exhausted",
    "quarantined",
    "rolled_back",
    "step4_failure_category",
    "step4_failure_classification",
)

_REASON_SEVERITY: dict[str, int] = {
    "hard_protected": 0,
    "blocked": 1,
    "step_cost_none": 2,
    "ok": 3,
}


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


def _bfs_reachable_from_stub(
    stub_cell: Coord,
    *,
    want_role: str,
    blocked: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    cheap_reuse_cells: frozenset[Coord] | None,
) -> set[Coord]:
    """Undirected reachability from ``stub_cell`` using STEP4 step legality (not costs)."""

    visited: set[Coord] = {stub_cell}
    q: deque[Coord] = deque([stub_cell])
    visits = 0
    while q:
        c = q.popleft()
        visits += 1
        if visits > _MAX_REACHABLE_GOAL_BFS_VISITS:
            break
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
            if v not in visited:
                visited.add(v)
                q.append(v)
    return visited


def _stub_neighbor_block_classification(
    near: list[dict[str, Any]],
) -> tuple[str | None, str | None, list[int] | None, str | None]:
    """Primary blocked_reason, near_stub string summary, nearest blocked cell, zone label."""

    bad_entries: list[tuple[int, str, list[int]]] = []
    reasons_seen: set[str] = set()
    for entry in near:
        if not isinstance(entry, dict):
            continue
        cell = entry.get("cell")
        reason = str(entry.get("reason") or "")
        if not isinstance(cell, list) or len(cell) < 2:
            continue
        if reason == "ok":
            continue
        reasons_seen.add(reason)
        x, y = int(cell[0]), int(cell[1])
        sev = _REASON_SEVERITY.get(reason, 99)
        bad_entries.append((sev, reason, [x, y]))
    if not bad_entries:
        return None, None, None, None
    bad_entries.sort(key=lambda t: (t[0], t[2][1], t[2][0]))
    _, primary_reason, nearest_cell = bad_entries[0]
    summary = "|".join(sorted(reasons_seen)) if reasons_seen else None
    return primary_reason, summary, nearest_cell, primary_reason


def build_routing_failure_detail_dict(
    *,
    extractor_id: str | None,
    placement_id: str | None,
    transport_kind: str | None,
    stub_cell: Coord,
    placement_commit_state: str | None,
    blocked_reason: str | None,
    blocked_reason_near_stub: str | None,
    nearest_blocked_cell: list[int] | None,
    nearest_blocked_zone: str | None,
    existing_trunk_present: bool,
    trunk_seed_candidate_count: int,
    route_goal_set_size: int,
    reachable_goal_count: int,
    reachable_existing_trunk_count: int,
    reachable_exterior_margin_count: int,
    candidate_expanded_nodes: int | None,
    search_mode: str | None,
    fallback_reason: str | None,
    search_budget_exhausted: bool,
    replacement_search_exhausted: bool | None,
    quarantined: bool,
    rolled_back: bool,
    step4_failure_category: str,
    step4_failure_classification: dict[str, Any],
) -> dict[str, Any]:
    """Normalized STEP4 routing failure telemetry (instrumentation-only contract)."""

    tk_out: str | None
    if transport_kind in ("shape_belt", "fluid_pipe"):
        tk_out = transport_kind
    elif transport_kind is None:
        tk_out = None
    else:
        tk_out = str(transport_kind)

    values: dict[str, Any] = {
        "extractor_id": extractor_id,
        "placement_id": placement_id,
        "transport_kind": tk_out,
        "stub_cell": [int(stub_cell[0]), int(stub_cell[1])],
        "placement_commit_state": placement_commit_state,
        "blocked_reason": blocked_reason,
        "blocked_reason_near_stub": blocked_reason_near_stub,
        "nearest_blocked_cell": nearest_blocked_cell,
        "nearest_blocked_zone": nearest_blocked_zone,
        "existing_trunk_present": bool(existing_trunk_present),
        "trunk_seed_candidate_count": int(trunk_seed_candidate_count),
        "route_goal_set_size": int(route_goal_set_size),
        "reachable_goal_count": int(reachable_goal_count),
        "reachable_existing_trunk_count": int(reachable_existing_trunk_count),
        "reachable_exterior_margin_count": int(reachable_exterior_margin_count),
        "candidate_expanded_nodes": candidate_expanded_nodes,
        "search_mode": search_mode,
        "fallback_reason": fallback_reason,
        "search_budget_exhausted": bool(search_budget_exhausted),
        "replacement_search_exhausted": replacement_search_exhausted,
        "quarantined": bool(quarantined),
        "rolled_back": bool(rolled_back),
        "step4_failure_category": step4_failure_category,
        "step4_failure_classification": dict(step4_failure_classification),
    }
    return {k: values[k] for k in ROUTING_FAILURE_DETAIL_KEYS}


def apply_routing_failure_detail_lifecycle(
    detail: dict[str, Any],
    *,
    replacement_search_exhausted: bool | None = None,
    quarantined: bool | None = None,
    rolled_back: bool | None = None,
    placement_commit_state: str | None = None,
) -> None:
    """Mutate ``detail['routing_failure_detail']`` in place (post-recovery / post-rollback)."""

    rfd = detail.get("routing_failure_detail")
    if not isinstance(rfd, dict):
        return
    if replacement_search_exhausted is not None:
        rfd["replacement_search_exhausted"] = replacement_search_exhausted
    if quarantined is not None:
        rfd["quarantined"] = quarantined
    if rolled_back is not None:
        rfd["rolled_back"] = rolled_back
    if placement_commit_state is not None:
        rfd["placement_commit_state"] = placement_commit_state


def sync_routing_failure_detail_placement_commit_state(fd: dict[str, Any], state: str) -> None:
    """Align ``placement_commit_state`` on ``routing_failure_detail`` with final FSM string."""

    seen: set[int] = set()
    for holder in (fd, fd.get("step4_route_failure_detail")):
        if not isinstance(holder, dict):
            continue
        rfd = holder.get("routing_failure_detail")
        if not isinstance(rfd, dict):
            continue
        i = id(rfd)
        if i in seen:
            continue
        seen.add(i)
        rfd["placement_commit_state"] = state


def patch_failure_row_routing_failure_detail_rolled_back(fd: dict[str, Any]) -> None:
    """Set ``rolled_back`` on ``routing_failure_detail`` (top-level and/or nested in detail)."""

    rfds: list[dict[str, Any]] = []
    top = fd.get("routing_failure_detail")
    if isinstance(top, dict):
        rfds.append(top)
    det = fd.get("step4_route_failure_detail")
    nested = det.get("routing_failure_detail") if isinstance(det, dict) else None
    if isinstance(nested, dict) and nested is not top:
        rfds.append(nested)
    for rfd in rfds:
        rfd["rolled_back"] = True


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
    trunk_seed_candidate_count: int | None = None,
    trunk_seed_cells: frozenset[Coord] | None = None,
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

    out: dict[str, Any] = {
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
        "search_mode": str(search_stats.get("search_mode") or "goal_cells_union_legacy"),
        "expanded_nodes": int(search_stats.get("expanded_nodes", 0)),
        "fallback_reason": None,
        "last_error": last_error,
    }
    _s4sd.copy_search_diagnostics_to_detail(out, search_stats)

    visited = _bfs_reachable_from_stub(
        stub_cell,
        want_role=want_role,
        blocked=blocked,
        cells=cells,
        mineable=mineable,
        asteroid=asteroid,
        is_external=is_external,
        cheap_reuse_cells=cheap_reuse_cells,
    )
    reachable_goals = frozenset(goal_cells & visited)
    reachable_trunk = reachable_goals & trunk_cells
    reachable_margin = reachable_goals & margin_cells

    blocked_reason, blocked_summary, nearest_blocked_cell, nearest_zone = (
        _stub_neighbor_block_classification(near)
    )
    tseed_n = int(trunk_seed_candidate_count or 0)
    ex_trunk = len(trunk_cells) > 0
    cand_nodes: int | None
    if "expanded_nodes" in search_stats:
        cand_nodes = int(search_stats["expanded_nodes"])
    else:
        cand_nodes = None
    search_budget_exhausted_flag = bool(stop == "budget")
    stm = search_stats.get("search_time_ms")
    search_time_ms_f: float | None
    if isinstance(stm, (int, float)):
        search_time_ms_f = float(stm)
    else:
        search_time_ms_f = None
    optimality: str | None
    if search_budget_exhausted_flag:
        optimality = None
    else:
        optimality = "dijkstra_positive_costs_shortest_within_heap_budget"

    cat = _s4fc.classify_step4_failure_category(
        stop_reason=str(stop) if stop is not None else None,
        last_error=last_error,
        nearest_transport_hops=nhops,
        near=near,
        goal_cells_count=len(goal_cells),
        reachable_goal_count=len(reachable_goals),
        cells=cells,
        want_role=want_role,
        stub_cell=stub_cell,
        hard_extras=hard_extras,
    )
    prot_hard = _s4fc.protected_corridor_hard_involved(
        near, stub_cell=stub_cell, hard_extras=hard_extras
    )
    goals_unreachable = len(goal_cells) > 0 and len(reachable_goals) == 0
    search_mode_s = str(out.get("search_mode") or "goal_cells_union_legacy")
    fallback_raw = out.get("fallback_reason")
    fallback_out: str | None = None if fallback_raw is None else str(fallback_raw)
    classification_sub = _s4fc.build_step4_failure_classification_dict(
        protected_corridor_hard_involved=prot_hard,
        all_goals_unreachable=goals_unreachable,
        search_budget_exhausted=search_budget_exhausted_flag,
        expanded_nodes=cand_nodes,
        search_time_ms=search_time_ms_f,
        search_mode=search_mode_s,
        fallback_reason=fallback_out,
        optimality_guarantee=optimality,
    )
    out["step4_failure_category"] = cat
    out["step4_failure_classification"] = classification_sub

    out["routing_failure_detail"] = build_routing_failure_detail_dict(
        extractor_id=placement_id,
        placement_id=placement_id,
        transport_kind=transport_kind,
        stub_cell=stub_cell,
        placement_commit_state=None,
        blocked_reason=blocked_reason,
        blocked_reason_near_stub=blocked_summary,
        nearest_blocked_cell=nearest_blocked_cell,
        nearest_blocked_zone=nearest_zone,
        existing_trunk_present=ex_trunk,
        trunk_seed_candidate_count=tseed_n,
        route_goal_set_size=len(goal_cells),
        reachable_goal_count=len(reachable_goals),
        reachable_existing_trunk_count=len(reachable_trunk),
        reachable_exterior_margin_count=len(reachable_margin),
        candidate_expanded_nodes=cand_nodes,
        search_mode=search_mode_s,
        fallback_reason=fallback_out,
        search_budget_exhausted=bool(stop == "budget"),
        replacement_search_exhausted=None,
        quarantined=False,
        rolled_back=False,
        step4_failure_category=cat,
        step4_failure_classification=classification_sub,
    )
    out["step4_replay_overlay"] = _s4rov.build_step4_row_replay_overlay(
        placement_id=placement_id,
        stub_cell=stub_cell,
        near=near,
        nearest_blocked_cell=nearest_blocked_cell,
        nearest_blocked_zone=nearest_zone,
        goal_cells=goal_cells,
        reachable_goals=reachable_goals,
        trunk_cells=trunk_cells,
        margin_cells=margin_cells,
        trunk_seed_cells=trunk_seed_cells,
    )
    return out
