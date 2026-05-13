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
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_dijkstra import (
    DIJKSTRA_REACHABLE_GOAL_COUNT_KEY,
    DIJKSTRA_REACHABLE_MARGIN_GOAL_COUNT_KEY,
    DIJKSTRA_REACHABLE_TRUNK_GOAL_COUNT_KEY,
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

# T1: flat top-level keys on every ``step4_route_failure_detail`` (debug NDJSON / replay rows).
# ``blocked_reason_near_stub`` remains the legacy neighbor list; string summary lives in rfd only.
STEP4_ROUTE_FAILURE_DETAIL_TOP_LEVEL_CANONICAL_KEYS: tuple[str, ...] = (
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
    "existing_trunk_goal_count",
    "external_goal_count",
    "reachable_goal_count",
    "reachable_existing_trunk_count",
    "reachable_exterior_margin_count",
    "candidate_expanded_nodes",
    "expanded_nodes",
    "search_mode",
    "fallback_reason",
    "search_budget_exhausted",
    "frontier_stop_reason",
    "last_error",
    "replacement_search_exhausted",
    "quarantined",
    "rolled_back",
    "step4_failure_category",
    "step4_failure_classification",
    "failure_detail_phase",
    "attempt_index",
    "rollback_reason",
    "rejected_reason",
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


def mirror_canonical_step4_route_failure_detail_top_level(detail: dict[str, Any]) -> None:
    """Copy ``routing_failure_detail`` scalars onto the top-level detail dict (T1 flat contract).

    Does not remove or replace the legacy ``blocked_reason_near_stub`` neighbor **list** when
    present. Classification dict is always a JSON object at top-level (empty dict if missing).
    """

    rfd = detail.get("routing_failure_detail")
    if not isinstance(rfd, dict):
        detail.setdefault("extractor_id", detail.get("placement_id"))
        detail.setdefault("placement_commit_state", None)
        detail.setdefault("blocked_reason", None)
        detail.setdefault("nearest_blocked_cell", None)
        detail.setdefault("nearest_blocked_zone", None)
        detail.setdefault("existing_trunk_present", False)
        detail.setdefault("trunk_seed_candidate_count", 0)
        detail.setdefault("route_goal_set_size", 0)
        detail.setdefault("reachable_goal_count", 0)
        detail.setdefault("reachable_existing_trunk_count", 0)
        detail.setdefault("reachable_exterior_margin_count", 0)
        detail.setdefault(
            "candidate_expanded_nodes", int(detail.get("expanded_nodes") or 0)
        )
        detail.setdefault("search_budget_exhausted", False)
        if "replacement_search_exhausted" not in detail:
            detail["replacement_search_exhausted"] = None
        detail.setdefault("quarantined", False)
        detail.setdefault("rolled_back", False)
        detail.setdefault("failure_detail_phase", None)
        detail.setdefault("attempt_index", 0)
        detail.setdefault("rollback_reason", None)
        detail.setdefault("rejected_reason", None)
        detail.setdefault("step4_failure_category", "unknown")
        if "step4_failure_classification" not in detail or not isinstance(
            detail.get("step4_failure_classification"), dict
        ):
            detail["step4_failure_classification"] = {}
        detail.setdefault("frontier_stop_reason", None)
        return

    ex_id = rfd.get("extractor_id")
    detail["extractor_id"] = ex_id if ex_id is not None else detail.get("placement_id")

    pid = rfd.get("placement_id")
    if pid is not None:
        detail["placement_id"] = pid

    tk = rfd.get("transport_kind")
    if tk is not None:
        detail["transport_kind"] = tk

    sc = rfd.get("stub_cell")
    if isinstance(sc, list) and len(sc) >= 2:
        detail["stub_cell"] = [int(sc[0]), int(sc[1])]

    detail["placement_commit_state"] = rfd.get("placement_commit_state")
    detail["blocked_reason"] = rfd.get("blocked_reason")
    detail["nearest_blocked_cell"] = rfd.get("nearest_blocked_cell")
    detail["nearest_blocked_zone"] = rfd.get("nearest_blocked_zone")
    detail["existing_trunk_present"] = bool(rfd.get("existing_trunk_present", False))
    detail["trunk_seed_candidate_count"] = int(rfd.get("trunk_seed_candidate_count") or 0)
    detail["route_goal_set_size"] = int(rfd.get("route_goal_set_size") or 0)

    detail["reachable_goal_count"] = int(rfd.get("reachable_goal_count") or 0)
    detail["reachable_existing_trunk_count"] = int(rfd.get("reachable_existing_trunk_count") or 0)
    detail["reachable_exterior_margin_count"] = int(
        rfd.get("reachable_exterior_margin_count") or 0
    )

    cand = rfd.get("candidate_expanded_nodes")
    if cand is not None:
        detail["candidate_expanded_nodes"] = int(cand)
    else:
        detail["candidate_expanded_nodes"] = int(detail.get("expanded_nodes") or 0)

    sm = rfd.get("search_mode")
    if sm is not None:
        detail["search_mode"] = str(sm)

    fb = rfd.get("fallback_reason")
    detail["fallback_reason"] = fb if fb is None else str(fb)

    detail["search_budget_exhausted"] = bool(rfd.get("search_budget_exhausted", False))

    rse = rfd.get("replacement_search_exhausted")
    detail["replacement_search_exhausted"] = rse if rse is None or isinstance(rse, bool) else None

    detail["quarantined"] = bool(rfd.get("quarantined", False))
    detail["rolled_back"] = bool(rfd.get("rolled_back", False))

    cat = rfd.get("step4_failure_category")
    detail["step4_failure_category"] = (
        str(cat) if cat is not None and str(cat).strip() else "unknown"
    )

    clf = rfd.get("step4_failure_classification")
    if isinstance(clf, dict):
        detail["step4_failure_classification"] = dict(clf)
    elif clf is None:
        detail["step4_failure_classification"] = {}
    else:
        detail["step4_failure_classification"] = {"raw": clf}

    if "frontier_stop_reason" not in detail:
        detail["frontier_stop_reason"] = None

    detail.setdefault("failure_detail_phase", None)
    detail.setdefault("attempt_index", 0)
    detail.setdefault("rollback_reason", None)
    detail.setdefault("rejected_reason", None)


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
    mirror_canonical_step4_route_failure_detail_top_level(detail)


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
    det = fd.get("step4_route_failure_detail")
    if isinstance(det, dict):
        mirror_canonical_step4_route_failure_detail_top_level(det)


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
    det = fd.get("step4_route_failure_detail")
    if isinstance(det, dict):
        mirror_canonical_step4_route_failure_detail_top_level(det)


def stamp_final_step4_route_failure_detail_trace_from_fd(
    fd: dict[str, Any],
    *,
    attempt_index: int,
) -> None:
    """T4: enrich ``step4_route_failure_detail`` after STEP4 cleanup (FSM-aligned).

    Caller must run after ``sync_routing_failure_detail_placement_commit_state`` /
    ``patch_failure_row_routing_failure_detail_rolled_back`` so nested
    ``routing_failure_detail`` already carries final ``placement_commit_state``,
    ``quarantined``, and ``rolled_back`` mirrored to the top level.
    """

    det = fd.get("step4_route_failure_detail")
    if not isinstance(det, dict):
        return
    det["failure_detail_phase"] = "final"
    det["attempt_index"] = int(attempt_index)
    rr = fd.get("rollback_reason")
    det["rollback_reason"] = None if rr is None else str(rr)
    rj = fd.get("rejected_reason")
    det["rejected_reason"] = None if rj is None else str(rj)


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
    placement_commit_state_at_route_attempt: str | None = None,
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
    reachable_trunk_bfs = reachable_goals & trunk_cells
    reachable_margin_bfs = reachable_goals & margin_cells

    dg = search_stats.get(DIJKSTRA_REACHABLE_GOAL_COUNT_KEY)
    if dg is not None:
        reachable_goal_count = int(dg)
        reachable_trunk_count = int(
            search_stats.get(DIJKSTRA_REACHABLE_TRUNK_GOAL_COUNT_KEY) or 0
        )
        reachable_margin_count = int(
            search_stats.get(DIJKSTRA_REACHABLE_MARGIN_GOAL_COUNT_KEY) or 0
        )
    else:
        reachable_goal_count = len(reachable_goals)
        reachable_trunk_count = len(reachable_trunk_bfs)
        reachable_margin_count = len(reachable_margin_bfs)

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

    search_mode_s = str(out.get("search_mode") or "goal_cells_union_legacy")
    fallback_raw = out.get("fallback_reason")
    fallback_out: str | None = None if fallback_raw is None else str(fallback_raw)

    frontier_sr = search_stats.get("frontier_stop_reason")
    if frontier_sr is None and stop is not None:
        frontier_sr = stop

    cat, conf, evidence = _s4fc.compute_step4_failure_classification(
        stop_reason=str(stop) if stop is not None else None,
        last_error=last_error,
        nearest_transport_hops=nhops,
        near=near,
        goal_cells_count=len(goal_cells),
        reachable_goal_count=reachable_goal_count,
        cells=cells,
        want_role=want_role,
        stub_cell=stub_cell,
        hard_extras=hard_extras,
        goal_cells=goal_cells,
        frontier_stop_reason=str(frontier_sr) if frontier_sr is not None else None,
        existing_trunk_present=ex_trunk,
        existing_trunk_goal_count=len(trunk_cells),
        reachable_existing_trunk_count=reachable_trunk_count,
        reachable_exterior_margin_count=reachable_margin_count,
        search_budget_exhausted=search_budget_exhausted_flag,
        expanded_nodes=cand_nodes,
    )
    prot_hard = _s4fc.protected_corridor_hard_involved(
        near, stub_cell=stub_cell, hard_extras=hard_extras
    )
    evidence["protected_corridor_hard_involved"] = bool(prot_hard)
    evidence["optimality_guarantee"] = optimality
    evidence["search_mode"] = search_mode_s
    evidence["search_time_ms"] = search_time_ms_f
    evidence["fallback_reason"] = fallback_out
    evidence["candidate_expanded_nodes"] = cand_nodes

    classification_sub = _s4fc.build_step4_failure_classification_dict(
        category=cat, confidence=conf, evidence=evidence
    )
    out["step4_failure_category"] = cat
    out["step4_failure_classification"] = classification_sub

    out["routing_failure_detail"] = build_routing_failure_detail_dict(
        extractor_id=placement_id,
        placement_id=placement_id,
        transport_kind=transport_kind,
        stub_cell=stub_cell,
        placement_commit_state=placement_commit_state_at_route_attempt,
        blocked_reason=blocked_reason,
        blocked_reason_near_stub=blocked_summary,
        nearest_blocked_cell=nearest_blocked_cell,
        nearest_blocked_zone=nearest_zone,
        existing_trunk_present=ex_trunk,
        trunk_seed_candidate_count=tseed_n,
        route_goal_set_size=len(goal_cells),
        reachable_goal_count=reachable_goal_count,
        reachable_existing_trunk_count=reachable_trunk_count,
        reachable_exterior_margin_count=reachable_margin_count,
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
    out.setdefault("frontier_stop_reason", None)
    mirror_canonical_step4_route_failure_detail_top_level(out)
    out["failure_detail_phase"] = None
    out["attempt_index"] = 0
    out["rollback_reason"] = None
    out["rejected_reason"] = None
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
