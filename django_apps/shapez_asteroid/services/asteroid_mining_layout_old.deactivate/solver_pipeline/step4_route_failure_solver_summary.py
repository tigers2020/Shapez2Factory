"""STEP4 route-failure aggregates for ``solver_summary`` (T5).

Aggregates are computed from ``Step4RoutingResult.routing_failures`` rows and embedded
``step4_route_failure_detail`` dicts only — never by re-reading NDJSON or trace files.

**Counts vs placements**

- ``step4_failure_attempt_detail_count`` — one per ``routing_failures`` row (list order).
- ``step4_failure_details_count`` — rows that carry a dict ``step4_route_failure_detail``.
- Histograms (category / last_error / …) — one increment per **detail row** (same row
  scanned once; missing detail contributes nothing to histograms).

Routing / placement / reclaim code must not consume these summary fields as algorithm input.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _sorted_str_int_dict(raw: dict[str, int]) -> dict[str, int]:
    return {k: int(raw[k]) for k in sorted(raw.keys())}


def _bucket_str(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    return s if s else ""


def _detail_dict(row: Mapping[str, Any]) -> dict[str, Any] | None:
    d = row.get("step4_route_failure_detail")
    return d if isinstance(d, dict) else None


def _rfd(detail: dict[str, Any]) -> dict[str, Any]:
    rfd = detail.get("routing_failure_detail")
    return rfd if isinstance(rfd, dict) else {}


def build_step4_route_failure_aggregate_for_solver_summary(
    routing_failures: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return T5 STEP4 failure telemetry fields for ``solver_summary``."""

    rows = list(routing_failures)
    attempt_detail_count = len(rows)

    failed_ids: set[str] = set()
    for row in rows:
        eid = row.get("extractor_id")
        if isinstance(eid, str) and eid.strip():
            failed_ids.add(eid)

    detail_rows: list[tuple[Mapping[str, Any], dict[str, Any]]] = []
    for row in rows:
        det = _detail_dict(row)
        if det is not None:
            detail_rows.append((row, det))

    failure_details_count = len(detail_rows)

    cat_c: dict[str, int] = {}
    last_c: dict[str, int] = {}
    frontier_c: dict[str, int] = {}
    mode_c: dict[str, int] = {}
    tk_c: dict[str, int] = {}
    reachable_zero_n = 0
    budget_ex_n = 0
    rolled_n = 0
    quarant_n = 0

    for row, det in detail_rows:
        rfd = _rfd(det)
        cat = det.get("step4_failure_category") or rfd.get("step4_failure_category")
        cat_key = _bucket_str(cat) or "unknown"
        cat_c[cat_key] = cat_c.get(cat_key, 0) + 1

        le = det.get("last_error")
        le_key = _bucket_str(le)
        last_c[le_key] = last_c.get(le_key, 0) + 1

        fs = det.get("frontier_stop_reason")
        if fs is None and rfd.get("frontier_stop_reason") is not None:
            fs = rfd.get("frontier_stop_reason")
        frontier_c[_bucket_str(fs) or ""] = frontier_c.get(_bucket_str(fs) or "", 0) + 1

        sm = det.get("search_mode") or rfd.get("search_mode")
        mode_c[_bucket_str(sm) or ""] = mode_c.get(_bucket_str(sm) or "", 0) + 1

        tk = det.get("transport_kind") or row.get("transport_kind") or rfd.get("transport_kind")
        tk_c[_bucket_str(tk) or ""] = tk_c.get(_bucket_str(tk) or "", 0) + 1

        rgc = det.get("reachable_goal_count")
        if rgc is None:
            rgc = rfd.get("reachable_goal_count")
        try:
            rgi = int(rgc) if rgc is not None else 0
        except (TypeError, ValueError):
            rgi = 0
        if rgi == 0:
            reachable_zero_n += 1

        sbe = det.get("search_budget_exhausted")
        if sbe is None:
            sbe = rfd.get("search_budget_exhausted")
        if bool(sbe):
            budget_ex_n += 1

        rb = det.get("rolled_back")
        if rb is None:
            rb = rfd.get("rolled_back")
        if bool(rb):
            rolled_n += 1

        qu = det.get("quarantined")
        if qu is None:
            qu = rfd.get("quarantined")
        if bool(qu):
            quarant_n += 1

    return {
        "step4_failed_placement_ids": sorted(failed_ids),
        "step4_failure_details_count": int(failure_details_count),
        "step4_failure_attempt_detail_count": int(attempt_detail_count),
        "step4_failed_placement_count": int(len(failed_ids)),
        "step4_route_failure_category_counts": _sorted_str_int_dict(cat_c),
        "step4_route_failure_last_error_counts": _sorted_str_int_dict(last_c),
        "step4_route_failure_frontier_stop_reason_counts": _sorted_str_int_dict(frontier_c),
        "step4_search_mode_counts": _sorted_str_int_dict(mode_c),
        "step4_failure_transport_kind_counts": _sorted_str_int_dict(tk_c),
        "step4_reachable_goal_zero_count": int(reachable_zero_n),
        "step4_search_budget_exhausted_count": int(budget_ex_n),
        "step4_rolled_back_failure_count": int(rolled_n),
        "step4_quarantined_failure_count": int(quarant_n),
    }


def empty_step4_route_failure_aggregate_for_solver_summary() -> dict[str, Any]:
    """Deterministic defaults when no ``routing_failures`` are available (exception path)."""

    return build_step4_route_failure_aggregate_for_solver_summary(())
