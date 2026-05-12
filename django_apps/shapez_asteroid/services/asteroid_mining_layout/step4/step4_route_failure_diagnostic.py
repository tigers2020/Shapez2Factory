"""Structured STEP4 route-failure diagnostics (Pass2 provisional → STEP4 Dijkstra)."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_ROUTE_LENGTH_RATIO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
)


class Step4RouteFailureReason(StrEnum):
    """Stable taxonomy for STEP4 routing failures (telemetry / replay)."""

    empty_goal_set = "empty_goal_set"
    no_exterior_margin_for_probe = "no_exterior_margin_for_probe"
    no_exterior_goal = "no_exterior_goal"
    no_trunk_seed_goal = "no_trunk_seed_goal"
    no_same_kind_route = "no_same_kind_route"
    mixed_transport_kind = "mixed_transport_kind"
    blocked_by_geometry = "blocked_by_geometry"
    blocked_by_hard_protected = "blocked_by_hard_protected"
    route_length_ratio_exceeded = "route_length_ratio_exceeded"
    search_budget_exhausted = "search_budget_exhausted"
    no_route_exhausted = "no_route_exhausted"
    unknown_route_failure = "unknown_route_failure"


def _blocked_category_counts(
    blocked: frozenset[Coord],
    *,
    stub_cell: Coord,
    hard_extras: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    want_role: str,
) -> tuple[int, int, int, int]:
    """Partition ``blocked`` (post stub discard) into body / wrong-role transport / hard / soft."""

    body = 0
    transport_wrong = 0
    hard_n = 0
    for c in blocked:
        if c == stub_cell:
            continue
        row = cells.get(c) or {}
        role = row.get("role")
        if c in hard_extras:
            hard_n += 1
        elif role in ("belt", "pipe") and role != want_role:
            transport_wrong += 1
        else:
            body += 1
    return body, transport_wrong, hard_n, 0


def _stub_neighbors_all_hard_protected(detail: dict[str, Any]) -> bool:
    near = detail.get("blocked_reason_near_stub")
    if not isinstance(near, list) or len(near) < 1:
        return False
    reasons = [str(x.get("reason", "")) for x in near if isinstance(x, dict)]
    return bool(reasons) and all(r == "hard_protected" for r in reasons)


def _stub_neighbors_geometry_blocked(detail: dict[str, Any]) -> bool:
    near = detail.get("blocked_reason_near_stub")
    if not isinstance(near, list) or len(near) < 1:
        return False
    bad = frozenset({"blocked", "step_cost_none"})
    reasons = [str(x.get("reason", "")) for x in near if isinstance(x, dict)]
    return bool(reasons) and all(r in bad for r in reasons)


def classify_step4_route_failure_reason(
    *,
    goal_count: int,
    exterior_goal_count: int,
    existing_trunk_goal_count: int,
    stub_cell_role_ok: bool,
    nearest_transport_hops: int | None,
    stop_reason: str | None,
    detail: dict[str, Any],
    route_length_ratio_exceeded: bool,
) -> Step4RouteFailureReason:
    """Best-effort single reason (first strong signal wins).

    Search exhaustion and ``last_error=no_route_exhausted`` are classified **before**
    ``mixed_transport_kind`` so void ``inferred`` stub roles do not mask real routing failures.
    """

    le = detail.get("last_error")
    last_err_s = str(le) if le is not None else ""

    if goal_count == 0:
        return Step4RouteFailureReason.empty_goal_set
    if route_length_ratio_exceeded:
        return Step4RouteFailureReason.route_length_ratio_exceeded
    if stop_reason == "budget":
        return Step4RouteFailureReason.search_budget_exhausted
    if nearest_transport_hops is None:
        return Step4RouteFailureReason.no_same_kind_route

    exhausted = stop_reason == "exhausted" or last_err_s == "no_route_exhausted"
    if exhausted:
        if _stub_neighbors_all_hard_protected(detail):
            return Step4RouteFailureReason.blocked_by_hard_protected
        if exterior_goal_count == 0 and existing_trunk_goal_count == 0:
            return Step4RouteFailureReason.no_exterior_goal
        if _stub_neighbors_geometry_blocked(detail):
            return Step4RouteFailureReason.blocked_by_geometry
        return Step4RouteFailureReason.no_route_exhausted

    if not stub_cell_role_ok:
        return Step4RouteFailureReason.mixed_transport_kind
    if _stub_neighbors_all_hard_protected(detail):
        return Step4RouteFailureReason.blocked_by_hard_protected
    if exterior_goal_count == 0 and existing_trunk_goal_count == 0:
        return Step4RouteFailureReason.no_exterior_goal
    if _stub_neighbors_geometry_blocked(detail):
        return Step4RouteFailureReason.blocked_by_geometry
    if stop_reason not in (None, "exhausted", "budget", "success"):
        return Step4RouteFailureReason.unknown_route_failure
    if stop_reason == "success":
        return Step4RouteFailureReason.unknown_route_failure
    return Step4RouteFailureReason.unknown_route_failure


def build_step4_route_failure_diagnostic(
    *,
    rec: PlacementCommitRecord | None,
    extractor_cell: Coord,
    stub_cell: Coord,
    transport_kind: str,
    want_role: str,
    raw_goal: set[Coord],
    goal_cells: frozenset[Coord],
    trunk_cells: frozenset[Coord],
    trunk_seed_candidates_by_kind: dict[str, set[Coord]],
    margin_cells: set[Coord],
    committed_trunk_for_kind: set[Coord],
    blocked: frozenset[Coord],
    hard_extras: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    cheap_reuse_cells: frozenset[Coord] | None,
    search_stats: dict[str, Any],
    detail: dict[str, Any],
    final_state: str | None,
) -> dict[str, Any]:
    """Stable nested dict: ``step4_route_failure_diagnostic`` on each ``routing_failures`` row."""

    _ = (raw_goal, mineable, asteroid, is_external, cheap_reuse_cells)
    goal_count = len(goal_cells)
    exterior_goal_count = len(goal_cells & margin_cells)
    seed_pool = trunk_seed_candidates_by_kind.get(transport_kind) or set()
    trunk_seed_goal_count = len(goal_cells & frozenset(seed_pool))
    existing_trunk_goal_count = len(trunk_cells)
    has_committed = bool(committed_trunk_for_kind)
    if has_committed:
        goal_set_kind = "committed_trunk_union_exterior_margin"
    else:
        goal_set_kind = "trunk_seed_candidates_union_exterior_margin"

    stub_row = cells.get(stub_cell)
    stub_role_ok = bool(stub_row and stub_row.get("role") == want_role)

    blocked_body_count, blocked_transport_count, protected_hard_count, protected_soft_count = (
        _blocked_category_counts(
            blocked,
            stub_cell=stub_cell,
            hard_extras=hard_extras,
            cells=cells,
            want_role=want_role,
        )
    )

    nhops = detail.get("nearest_existing_transport_distance")
    nearest_hops = int(nhops) if isinstance(nhops, int) else None

    stop_reason = search_stats.get("stop_reason")
    if not isinstance(stop_reason, str):
        stop_reason = None

    ratio_exceeded = bool(search_stats.get("route_length_ratio_exceeded"))

    last_error = str(detail.get("last_error") or "no_route")

    failure_reason = classify_step4_route_failure_reason(
        goal_count=goal_count,
        exterior_goal_count=exterior_goal_count,
        existing_trunk_goal_count=existing_trunk_goal_count,
        stub_cell_role_ok=stub_role_ok,
        nearest_transport_hops=nearest_hops,
        stop_reason=stop_reason,
        detail=detail,
        route_length_ratio_exceeded=ratio_exceeded,
    )

    search_exhausted = stop_reason == "exhausted" or last_error == "no_route_exhausted"
    search_mode = str(search_stats.get("search_mode") or "goal_cells_union_legacy")
    expanded_nodes = int(search_stats.get("expanded_nodes", 0))
    search_time_ms = search_stats.get("search_time_ms")
    if isinstance(search_time_ms, (int, float)):
        search_time_ms_f = float(search_time_ms)
    else:
        search_time_ms_f = 0.0

    placement_id = rec.placement_id if rec is not None else detail.get("placement_id")
    placement_pass = rec.placement_pass if rec is not None else None

    st_final: str | None = final_state
    if st_final is None and rec is not None:
        st = rec.state
        st_final = st.value if isinstance(st, PlacementCommitState) else str(st)

    return {
        "failure_reason": failure_reason.value,
        "placement_id": placement_id,
        "placement_pass": placement_pass,
        "extractor_cell": [int(extractor_cell[0]), int(extractor_cell[1])],
        "stub_cell": [int(stub_cell[0]), int(stub_cell[1])],
        "transport_kind": transport_kind,
        "goal_set_kind": goal_set_kind,
        "goal_count": goal_count,
        "exterior_goal_count": exterior_goal_count,
        "trunk_seed_goal_count": trunk_seed_goal_count,
        "existing_trunk_goal_count": existing_trunk_goal_count,
        "blocked_body_count": blocked_body_count,
        "blocked_transport_count": blocked_transport_count,
        "protected_hard_count": protected_hard_count,
        "protected_soft_count": protected_soft_count,
        "baseline_route_length": nearest_hops,
        "candidate_route_length": None,
        "route_length_ratio_limit": float(MAX_ROUTE_LENGTH_RATIO),
        "search_mode": search_mode,
        "expanded_nodes": expanded_nodes,
        "search_time_ms": search_time_ms_f,
        "search_exhausted": search_exhausted,
        "final_state": st_final,
        "last_error": last_error,
        "stub_cell_role_ok": stub_role_ok,
        "stub_role": None if stub_row is None else stub_row.get("role"),
        "expected_stub_role": want_role,
        "classifier_inputs": {
            "goal_count": goal_count,
            "exterior_goal_count": exterior_goal_count,
            "existing_trunk_goal_count": existing_trunk_goal_count,
            "stub_cell_role_ok": stub_role_ok,
            "nearest_transport_hops": nearest_hops,
            "stop_reason": stop_reason,
            "last_error": last_error,
            "route_length_ratio_exceeded": ratio_exceeded,
        },
    }


def build_step4_route_failure_diagnostic_p2c(
    *,
    rec: PlacementCommitRecord,
    reason: str,
    final_state: str,
) -> dict[str, Any]:
    """Minimal diagnostic when P2-C cascade rollback appends a routing failure (no Dijkstra row)."""

    ext = rec.extractor_cell
    stub = rec.stub_cell
    return {
        "failure_reason": Step4RouteFailureReason.unknown_route_failure.value,
        "placement_id": rec.placement_id,
        "placement_pass": rec.placement_pass,
        "extractor_cell": [int(ext[0]), int(ext[1])],
        "stub_cell": [int(stub[0]), int(stub[1])],
        "transport_kind": rec.transport_kind,
        "goal_set_kind": None,
        "goal_count": 0,
        "exterior_goal_count": 0,
        "trunk_seed_goal_count": 0,
        "existing_trunk_goal_count": 0,
        "blocked_body_count": 0,
        "blocked_transport_count": 0,
        "protected_hard_count": 0,
        "protected_soft_count": 0,
        "baseline_route_length": None,
        "candidate_route_length": None,
        "route_length_ratio_limit": float(MAX_ROUTE_LENGTH_RATIO),
        "search_mode": "p2c_cascade",
        "expanded_nodes": 0,
        "search_time_ms": 0.0,
        "search_exhausted": False,
        "final_state": final_state,
        "last_error": reason,
    }
