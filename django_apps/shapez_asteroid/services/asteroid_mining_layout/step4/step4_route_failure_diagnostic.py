"""Structured STEP4 route-failure diagnostics (Pass2 provisional → STEP4 Dijkstra)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
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
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_search_diagnostics as _s4sd,
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


def is_hard_protected_stub_ring_failure(detail: Mapping[str, Any] | None) -> bool:
    """True when every stub-adjacent cell is classified ``hard_protected`` (ring / cage class)."""

    if not isinstance(detail, Mapping):
        return False
    return _stub_neighbors_all_hard_protected(dict(detail))


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


_STEP4_NO_ROUTE_EXHAUSTED_EMPTY: dict[str, Any] = {
    "count": 0,
    "by_transport_kind": {},
    "by_placement_pass": {},
    "by_nearest_transport_hops": {},
    "by_blocked_reason_near_stub": {},
    "by_goal_count": {},
    "by_existing_trunk_goal_count": {},
    "by_protected_hard_count": {},
    "by_protected_soft_count": {},
    "by_expanded_nodes_bucket": {},
    "expanded_nodes": {"min": None, "max": None, "mean": None},
    "by_breaker_category": {},
    "dominant_blocker_category": None,
    "sample_rows": [],
}

_STEP4_NO_ROUTE_SAMPLE_MAX = 6

_BREAKER_CATEGORY_ORDER: tuple[str, ...] = (
    "hard_protected_ring",
    "stub_local_geometry_or_corridor",
    "trunk_union_goals_unreachable_from_stub",
    "wide_search_exhausted",
    "narrow_search_exhausted",
    "other_no_route_exhausted",
)


def _extract_step4_failure_diagnostic(row: Mapping[str, Any]) -> dict[str, Any] | None:
    d = row.get("step4_route_failure_diagnostic")
    if isinstance(d, dict):
        return d
    det = row.get("step4_route_failure_detail")
    if isinstance(det, dict):
        d2 = det.get("step4_route_failure_diagnostic")
        if isinstance(d2, dict):
            return d2
    return None


def _extract_step4_failure_detail(row: Mapping[str, Any]) -> dict[str, Any]:
    det = row.get("step4_route_failure_detail")
    if isinstance(det, dict):
        return det
    return {}


def _hist_str_key_scalar(val: Any) -> str:
    if val is None:
        return "missing"
    if type(val) is int and not isinstance(val, bool):
        return str(val)
    if isinstance(val, str) and val:
        return val
    return "missing"


def _nearest_transport_hops_hist_key(diag: dict[str, Any], detail: dict[str, Any]) -> str:
    ci = diag.get("classifier_inputs")
    if isinstance(ci, dict):
        h = ci.get("nearest_transport_hops")
        if type(h) is int and not isinstance(h, bool):
            return str(h)
    d = detail.get("nearest_existing_transport_distance")
    if type(d) is int and not isinstance(d, bool):
        return str(d)
    return "missing"


def _blocked_near_stub_signature(detail: dict[str, Any]) -> str:
    near = detail.get("blocked_reason_near_stub")
    if not isinstance(near, list) or not near:
        return "missing"
    items: list[tuple[int, int, str]] = []
    for e in near:
        if not isinstance(e, dict):
            return "missing"
        cell = e.get("cell")
        if not isinstance(cell, (list, tuple)) or len(cell) != 2:
            return "missing"
        try:
            x, y = int(cell[0]), int(cell[1])
        except (TypeError, ValueError):
            return "missing"
        items.append((y, x, str(e.get("reason", ""))))
    if not items:
        return "missing"
    items.sort(key=lambda t: (t[0], t[1], t[2]))
    return "|".join(f"{x},{y}:{reason}" for y, x, reason in items)


def _expanded_nodes_bucket(n: int) -> str:
    if n <= 1:
        return "0-1"
    if n <= 7:
        return "2-7"
    if n <= 32:
        return "8-32"
    return "33+"


def _expanded_nodes_int(diag: dict[str, Any]) -> int | None:
    v = diag.get("expanded_nodes")
    return v if type(v) is int and not isinstance(v, bool) else None


def _row_breaker_category_no_route_exhausted(diag: dict[str, Any], detail: dict[str, Any]) -> str:
    if _stub_neighbors_all_hard_protected(detail):
        return "hard_protected_ring"
    if _stub_neighbors_geometry_blocked(detail):
        return "stub_local_geometry_or_corridor"
    ext = int(diag.get("exterior_goal_count") or 0)
    et = int(diag.get("existing_trunk_goal_count") or 0)
    if ext == 0 and et > 0:
        return "trunk_union_goals_unreachable_from_stub"
    exn = _expanded_nodes_int(diag)
    if exn is not None and exn >= 20:
        return "wide_search_exhausted"
    if exn is not None and exn <= 7:
        return "narrow_search_exhausted"
    return "other_no_route_exhausted"


def _dominant_breaker_category(by_breaker: Counter[str]) -> str | None:
    if not by_breaker:
        return None
    max_n = max(by_breaker.values())
    tied = [k for k, v in by_breaker.items() if v == max_n]
    for cat in _BREAKER_CATEGORY_ORDER:
        if cat in tied:
            return cat
    return tied[0]


def _no_route_exhausted_sample_row(
    row: Mapping[str, Any], diag: dict[str, Any], detail: dict[str, Any]
) -> dict[str, Any]:
    """Human-readable subset for UI / NDJSON (not used by routing)."""

    pid = row.get("placement_id")
    if pid is None:
        pid = row.get("extractor_id")
    sc = row.get("stub_cell")
    ec = row.get("extractor_cell")
    stub_cell: list[int] | None = None
    extractor_cell: list[int] | None = None
    if isinstance(sc, (list, tuple)) and len(sc) == 2:
        try:
            stub_cell = [int(sc[0]), int(sc[1])]
        except (TypeError, ValueError):
            stub_cell = None
    if isinstance(ec, (list, tuple)) and len(ec) == 2:
        try:
            extractor_cell = [int(ec[0]), int(ec[1])]
        except (TypeError, ValueError):
            extractor_cell = None
    near_raw = detail.get("blocked_reason_near_stub")
    blocked_near_stub: list[dict[str, Any]] = []
    if isinstance(near_raw, list):
        for e in near_raw[:4]:
            if not isinstance(e, dict):
                continue
            cell = e.get("cell")
            if not isinstance(cell, (list, tuple)) or len(cell) != 2:
                continue
            try:
                blocked_near_stub.append(
                    {
                        "x": int(cell[0]),
                        "y": int(cell[1]),
                        "reason": str(e.get("reason", "")),
                    }
                )
            except (TypeError, ValueError):
                continue
    return {
        "placement_id": pid,
        "stub_cell": stub_cell,
        "extractor_cell": extractor_cell,
        "transport_kind": diag.get("transport_kind"),
        "placement_pass": diag.get("placement_pass"),
        "breaker_category": _row_breaker_category_no_route_exhausted(diag, detail),
        "goal_count": diag.get("goal_count"),
        "existing_trunk_goal_count": diag.get("existing_trunk_goal_count"),
        "exterior_goal_count": diag.get("exterior_goal_count"),
        "blocked_near_stub": blocked_near_stub,
    }


def breaker_category_for_no_route_exhausted(
    diag: Mapping[str, Any], detail: Mapping[str, Any]
) -> str:
    """Stable breaker label for ``no_route_exhausted`` rows (local bridge trigger audit)."""

    return _row_breaker_category_no_route_exhausted(dict(diag), dict(detail))


def _sorted_histogram(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def build_step4_no_route_exhausted_breakdown(
    failures: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate routing failure rows with ``failure_reason=no_route_exhausted`` (telemetry)."""

    rows: list[tuple[Mapping[str, Any], dict[str, Any], dict[str, Any]]] = []
    for row in failures:
        diag = _extract_step4_failure_diagnostic(row)
        if diag is None:
            continue
        if diag.get("failure_reason") != Step4RouteFailureReason.no_route_exhausted.value:
            continue
        detail = _extract_step4_failure_detail(row)
        rows.append((row, diag, detail))

    n = len(rows)
    if n == 0:
        return dict(_STEP4_NO_ROUTE_EXHAUSTED_EMPTY)

    by_tk: Counter[str] = Counter()
    by_pass: Counter[str] = Counter()
    by_hops: Counter[str] = Counter()
    by_sig: Counter[str] = Counter()
    by_goal: Counter[str] = Counter()
    by_trunk_goal: Counter[str] = Counter()
    by_hard: Counter[str] = Counter()
    by_soft: Counter[str] = Counter()
    by_bucket: Counter[str] = Counter()
    by_breaker: Counter[str] = Counter()
    exp_vals: list[int] = []

    sample_rows: list[dict[str, Any]] = []
    for row, diag, detail in rows:
        tk = diag.get("transport_kind")
        by_tk[_hist_str_key_scalar(tk if isinstance(tk, str) and tk else None)] += 1

        pp = diag.get("placement_pass")
        if pp is None:
            by_pass["missing"] += 1
        else:
            by_pass[str(pp)] += 1

        by_hops[_nearest_transport_hops_hist_key(diag, detail)] += 1
        by_sig[_blocked_near_stub_signature(detail)] += 1
        by_goal[_hist_str_key_scalar(diag.get("goal_count"))] += 1
        by_trunk_goal[_hist_str_key_scalar(diag.get("existing_trunk_goal_count"))] += 1
        by_hard[_hist_str_key_scalar(diag.get("protected_hard_count"))] += 1
        by_soft[_hist_str_key_scalar(diag.get("protected_soft_count"))] += 1

        exn = _expanded_nodes_int(diag)
        if exn is None:
            by_bucket["missing"] += 1
        else:
            by_bucket[_expanded_nodes_bucket(exn)] += 1
            exp_vals.append(exn)

        by_breaker[_row_breaker_category_no_route_exhausted(diag, detail)] += 1
        if len(sample_rows) < _STEP4_NO_ROUTE_SAMPLE_MAX:
            sample_rows.append(_no_route_exhausted_sample_row(row, diag, detail))

    if exp_vals:
        mn, mx = min(exp_vals), max(exp_vals)
        mean_f = round(sum(exp_vals) / len(exp_vals), 4)
    else:
        mn = mx = mean_f = None  # type: ignore[assignment]

    return {
        "count": n,
        "by_transport_kind": _sorted_histogram(by_tk),
        "by_placement_pass": _sorted_histogram(by_pass),
        "by_nearest_transport_hops": _sorted_histogram(by_hops),
        "by_blocked_reason_near_stub": _sorted_histogram(by_sig),
        "by_goal_count": _sorted_histogram(by_goal),
        "by_existing_trunk_goal_count": _sorted_histogram(by_trunk_goal),
        "by_protected_hard_count": _sorted_histogram(by_hard),
        "by_protected_soft_count": _sorted_histogram(by_soft),
        "by_expanded_nodes_bucket": _sorted_histogram(by_bucket),
        "expanded_nodes": {
            "min": mn if exp_vals else None,
            "max": mx if exp_vals else None,
            "mean": mean_f if exp_vals else None,
        },
        "by_breaker_category": _sorted_histogram(by_breaker),
        "dominant_blocker_category": _dominant_breaker_category(by_breaker),
        "sample_rows": sample_rows,
    }


_STEP4_HARD_PROTECTED_NO_ROUTE_EMPTY: dict[str, Any] = {
    "count": 0,
    "by_transport_kind": {},
    "by_placement_pass": {},
    "same_kind_trunk_beyond_protected": {"true": 0, "false": 0},
    "hard_protected_neighbors_near_stub": {"min": None, "max": None, "mean": None},
    "bypass_candidate_total": 0,
    "soft_replace_candidate_total": 0,
    "sample_traces": [],
}


def build_step4_hard_protected_no_route_breakdown(
    failures: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate ``step4_hard_protected_no_route_trace`` rows (hard stub ring telemetry)."""

    rows: list[tuple[dict[str, Any], Mapping[str, Any]]] = []
    for row in failures:
        tr = row.get("step4_hard_protected_no_route_trace")
        if isinstance(tr, dict) and tr:
            rows.append((tr, row))

    n = len(rows)
    if n == 0:
        return dict(_STEP4_HARD_PROTECTED_NO_ROUTE_EMPTY)

    by_tk: Counter[str] = Counter()
    by_pass: Counter[str] = Counter()
    beyond_t = 0
    beyond_f = 0
    hard_vals: list[int] = []
    bypass_sum = 0
    soft_sum = 0
    sample_traces: list[dict[str, Any]] = []

    for tr, row in rows:
        tk = row.get("transport_kind")
        by_tk[_hist_str_key_scalar(tk if isinstance(tk, str) and tk else None)] += 1

        diag = _extract_step4_failure_diagnostic(row)
        pp = diag.get("placement_pass") if isinstance(diag, dict) else None
        if pp is None:
            by_pass["missing"] += 1
        else:
            by_pass[str(pp)] += 1

        if tr.get("same_kind_trunk_beyond_protected") is True:
            beyond_t += 1
        else:
            beyond_f += 1

        hn = tr.get("hard_protected_neighbors_near_stub")
        if type(hn) is int:
            hard_vals.append(hn)
        bypass_sum += int(tr.get("bypass_candidate_count") or 0)
        soft_sum += int(tr.get("soft_replace_candidate_count") or 0)

        if len(sample_traces) < 6:
            smp = dict(tr)
            pid = row.get("extractor_id")
            if isinstance(diag, dict) and diag.get("placement_id") is not None:
                pid = diag.get("placement_id")
            smp["placement_id"] = pid
            sample_traces.append(smp)

    if hard_vals:
        mn, mx = min(hard_vals), max(hard_vals)
        mean_f = round(sum(hard_vals) / len(hard_vals), 4)
    else:
        mn = mx = mean_f = None  # type: ignore[assignment]

    return {
        "count": n,
        "by_transport_kind": _sorted_histogram(by_tk),
        "by_placement_pass": _sorted_histogram(by_pass),
        "same_kind_trunk_beyond_protected": {"true": beyond_t, "false": beyond_f},
        "hard_protected_neighbors_near_stub": {
            "min": mn if hard_vals else None,
            "max": mx if hard_vals else None,
            "mean": mean_f if hard_vals else None,
        },
        "bypass_candidate_total": bypass_sum,
        "soft_replace_candidate_total": soft_sum,
        "sample_traces": sample_traces,
    }


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

    out: dict[str, Any] = {
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
    out.update(_s4sd.search_stats_diagnostic_extras(search_stats))
    return out


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
