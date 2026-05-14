"""Pass3 zero-gain telemetry: reject buckets, outcome vs summary (S5).

Buckets are API-stable snake_case strings used in ``pass3_reject_by_reason`` and logs.
Counts may reflect multiple diagnostic sources (atomic, greedy, local reroute) in one run.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P3E3_REJECT_CONNECTIVITY,
    P3E3_REJECT_DISCONNECTED_STUB,
    P3E3_REJECT_EXTERNAL_UNREACHABLE_TRANSPORT,
    P3E3_REJECT_FIXED_STUB_REMOVAL,
    P3E3_REJECT_GEOMETRY,
    P3E3_REJECT_HARD_PROTECTED_CORRIDOR,
    P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN,
    P3E3_REJECT_NO_REPLACEMENT_ROUTE,
    P3E3_REJECT_ORPHAN_TRANSPORT,
    P3E3_REJECT_PRECHECK_NO_CANDIDATE,
    P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
    P3E3_REJECT_ROUTE_LENGTH_RATIO,
    P3E3_REJECT_VALIDATION,
    PASS3_GREEDY_REJECT_DETAIL_CONNECTIVITY,
    PASS3_GREEDY_REJECT_DETAIL_NO_INTERNAL_DELTA,
    PASS3_GREEDY_REJECT_DETAIL_ROUTE_LENGTH_RATIO,
    PASS3_GREEDY_REJECT_DETAIL_ZERO_GAIN,
)

PASS3_OUTCOME_SKIPPED = "skipped"
PASS3_OUTCOME_IMPROVED = "improved"
PASS3_OUTCOME_NO_CANDIDATES = "no_candidates"
PASS3_OUTCOME_CANDIDATES_REJECTED = "candidates_rejected"

PASS3_REJECT_NO_INTERNAL_TRANSPORT_SAVING = "no_internal_transport_saving"
PASS3_REJECT_CONNECTIVITY_BREAK = "connectivity_break"
PASS3_REJECT_HARD_PROTECTED_BLOCK = "hard_protected_block"
PASS3_REJECT_NO_REPLACEMENT_ROUTE = "no_replacement_route"
PASS3_REJECT_LENGTH_RATIO_EXCEEDED = "length_ratio_exceeded"
PASS3_REJECT_SEARCH_BUDGET_EXCEEDED = "search_budget_exceeded"
PASS3_REJECT_SAME_KIND_GOAL_UNREACHABLE = "same_kind_goal_unreachable"
PASS3_REJECT_SOFT_REPLACE_NOT_ATOMIC = "soft_replace_not_atomic"
PASS3_REJECT_GEOMETRY_BLOCKED = "geometry_blocked"

PASS3_REJECT_BY_REASON_BUCKETS: tuple[str, ...] = (
    PASS3_REJECT_NO_INTERNAL_TRANSPORT_SAVING,
    PASS3_REJECT_CONNECTIVITY_BREAK,
    PASS3_REJECT_HARD_PROTECTED_BLOCK,
    PASS3_REJECT_NO_REPLACEMENT_ROUTE,
    PASS3_REJECT_LENGTH_RATIO_EXCEEDED,
    PASS3_REJECT_SEARCH_BUDGET_EXCEEDED,
    PASS3_REJECT_SAME_KIND_GOAL_UNREACHABLE,
    PASS3_REJECT_SOFT_REPLACE_NOT_ATOMIC,
    PASS3_REJECT_GEOMETRY_BLOCKED,
)

PASS3_ZERO_GAIN_TELEMETRY_KEYS: frozenset[str] = frozenset(
    {
        "pass3_zero_gain_outcome",
        "pass3_zero_gain_summary",
        "pass3_reject_by_reason",
        "pass3_candidate_route_count",
        "pass3_candidate_improved_count",
        "pass3_best_candidate_delta",
        "pass3_best_candidate_rejected_reason",
        "pass3_goal_set_count_by_kind",
        "pass3_search_mode_counts",
        "pass3_reject_sample_rows",
        "pass3_transport_kind",
        "pass3_routing_job_count",
    }
)

_MAX_SAMPLE_ROWS = 8


def _empty_reject_by_reason() -> dict[str, int]:
    return {b: 0 for b in PASS3_REJECT_BY_REASON_BUCKETS}


def _bump(dst: dict[str, int], bucket: str, n: int = 1) -> None:
    if bucket not in dst:
        return
    dst[bucket] = int(dst[bucket]) + int(n)


def bucket_for_p3e3_reason(reason: str | None) -> str | None:
    if not reason:
        return None
    if reason in (P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN,):
        return PASS3_REJECT_NO_INTERNAL_TRANSPORT_SAVING
    if reason in (
        P3E3_REJECT_CONNECTIVITY,
        P3E3_REJECT_DISCONNECTED_STUB,
        P3E3_REJECT_ORPHAN_TRANSPORT,
        P3E3_REJECT_EXTERNAL_UNREACHABLE_TRANSPORT,
        P3E3_REJECT_VALIDATION,
    ):
        return PASS3_REJECT_CONNECTIVITY_BREAK
    if reason in (P3E3_REJECT_HARD_PROTECTED_CORRIDOR, P3E3_REJECT_FIXED_STUB_REMOVAL):
        return PASS3_REJECT_HARD_PROTECTED_BLOCK
    if reason in (
        P3E3_REJECT_NO_REPLACEMENT_ROUTE,
        P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
    ):
        return PASS3_REJECT_NO_REPLACEMENT_ROUTE
    if reason == P3E3_REJECT_ROUTE_LENGTH_RATIO:
        return PASS3_REJECT_LENGTH_RATIO_EXCEEDED
    if reason == P3E3_REJECT_PRECHECK_NO_CANDIDATE:
        return PASS3_REJECT_SAME_KIND_GOAL_UNREACHABLE
    if reason == P3E3_REJECT_GEOMETRY:
        return PASS3_REJECT_GEOMETRY_BLOCKED
    low = reason.lower()
    if "hard_protected" in low or "fixed_stub" in low:
        return PASS3_REJECT_HARD_PROTECTED_BLOCK
    if "replacement" in low or "precheck_no_replacement" in low:
        return PASS3_REJECT_NO_REPLACEMENT_ROUTE
    if "ratio" in low or "route_length" in low:
        return PASS3_REJECT_LENGTH_RATIO_EXCEEDED
    if (
        "connectivity" in low
        or "disconnected" in low
        or "orphan" in low
        or "external_unreachable" in low
    ):
        return PASS3_REJECT_CONNECTIVITY_BREAK
    if "geometry" in low:
        return PASS3_REJECT_GEOMETRY_BLOCKED
    if "no_internal" in low or "internal_transport_gain" in low:
        return PASS3_REJECT_NO_INTERNAL_TRANSPORT_SAVING
    return None


def bucket_for_shadow_rejected(shadow_reason: str | None) -> str | None:
    if not shadow_reason:
        return None
    if shadow_reason == "lex_hard_protected_hit":
        return PASS3_REJECT_HARD_PROTECTED_BLOCK
    if shadow_reason == "lex_length_over_ratio_vs_greedy":
        return PASS3_REJECT_LENGTH_RATIO_EXCEEDED
    if shadow_reason == "lex_blocked_cell_on_path":
        return PASS3_REJECT_GEOMETRY_BLOCKED
    if shadow_reason in ("lex_not_found", "no_greedy_baseline"):
        return PASS3_REJECT_SAME_KIND_GOAL_UNREACHABLE
    if shadow_reason == "no_internal_transport_improvement":
        return PASS3_REJECT_NO_INTERNAL_TRANSPORT_SAVING
    if shadow_reason.startswith("precheck_shadow_"):
        inner = shadow_reason.removeprefix("precheck_shadow_")
        if inner == "lex_not_found":
            return PASS3_REJECT_SAME_KIND_GOAL_UNREACHABLE
        if inner == "no_internal_transport_improvement":
            return PASS3_REJECT_NO_INTERNAL_TRANSPORT_SAVING
        return bucket_for_shadow_rejected(inner)
    return None


def bucket_for_lex_fallback(fallback: str | None) -> str | None:
    if fallback == "expanded_node_budget_exceeded":
        return PASS3_REJECT_SEARCH_BUDGET_EXCEEDED
    if fallback == "no_route_to_goals":
        return PASS3_REJECT_SAME_KIND_GOAL_UNREACHABLE
    return None


def bucket_for_greedy_detail(detail: str | None) -> str | None:
    if not detail:
        return None
    if detail == PASS3_GREEDY_REJECT_DETAIL_NO_INTERNAL_DELTA:
        return PASS3_REJECT_NO_INTERNAL_TRANSPORT_SAVING
    if detail == PASS3_GREEDY_REJECT_DETAIL_CONNECTIVITY:
        return PASS3_REJECT_CONNECTIVITY_BREAK
    if detail == PASS3_GREEDY_REJECT_DETAIL_ROUTE_LENGTH_RATIO:
        return PASS3_REJECT_LENGTH_RATIO_EXCEEDED
    if detail == PASS3_GREEDY_REJECT_DETAIL_ZERO_GAIN:
        return PASS3_REJECT_NO_INTERNAL_TRANSPORT_SAVING
    return None


def aggregate_pass3_reject_by_reason(trace: Mapping[str, Any]) -> dict[str, int]:
    out = _empty_reject_by_reason()
    raw_chain: list[str | None] = [
        trace.get("p3f_rejected_reason_raw"),
        trace.get("p3f_rejected_reason"),
        trace.get("p3e3_internal_transport_delta_gate_reject"),
        trace.get("p3e3_guarded_commit_rejected_reason"),
    ]
    for r in raw_chain:
        if isinstance(r, str) and r.strip():
            b = bucket_for_p3e3_reason(r)
            if b:
                _bump(out, b, 1)

    gdetail = trace.get("pass3_greedy_reject_detail")
    b_g = bucket_for_greedy_detail(gdetail if isinstance(gdetail, str) else None)
    if b_g and int(trace.get("pass3_internal_transport_saved") or 0) <= 0:
        _bump(out, b_g, 1)

    shadow_r = trace.get("p3e2_shadow_rejected_reason")
    b_s = bucket_for_shadow_rejected(shadow_r if isinstance(shadow_r, str) else None)
    if b_s:
        _bump(out, b_s, 1)

    fb = trace.get("p3e2_lex_fallback_reason_last")
    b_f = bucket_for_lex_fallback(fb if isinstance(fb, str) else None)
    if b_f:
        _bump(out, b_f, 1)

    lr = trace.get("pass3_greedy_local_replacement")
    if isinstance(lr, dict):
        _bump(out, PASS3_REJECT_NO_REPLACEMENT_ROUTE, int(lr.get("rejected_by_no_path") or 0))
        _bump(out, PASS3_REJECT_LENGTH_RATIO_EXCEEDED, int(lr.get("rejected_by_path_len") or 0))
        _bump(
            out,
            PASS3_REJECT_SEARCH_BUDGET_EXCEEDED,
            int(lr.get("rejected_by_disconnected_stub_limit") or 0),
        )
        _bump(
            out,
            PASS3_REJECT_NO_INTERNAL_TRANSPORT_SAVING,
            int(lr.get("rejected_by_no_net_internal_gain") or 0),
        )

    return out


def classify_pass3_zero_gain_outcome(trace: Mapping[str, Any]) -> str | None:
    if bool(trace.get("pass3_skipped")):
        return PASS3_OUTCOME_SKIPPED
    saved = int(trace.get("pass3_internal_transport_saved") or 0)
    if saved > 0:
        return PASS3_OUTCOME_IMPROVED

    raw = trace.get("p3f_rejected_reason_raw")
    raw_s = raw if isinstance(raw, str) else None
    atomic_skipped = trace.get("p3e3_guarded_atomic_skipped_reason")
    cand_kinds = int(trace.get("p3f_candidate_kind_count") or 0)
    greedy_detail = trace.get("pass3_greedy_reject_detail")

    if raw_s == P3E3_REJECT_PRECHECK_NO_CANDIDATE:
        return PASS3_OUTCOME_NO_CANDIDATES
    if raw_s == P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE and cand_kinds == 0:
        return PASS3_OUTCOME_NO_CANDIDATES
    if (
        isinstance(atomic_skipped, str)
        and atomic_skipped
        and trace.get("p3e3_atomic_candidate_built") is None
        and cand_kinds == 0
        and greedy_detail == PASS3_GREEDY_REJECT_DETAIL_NO_INTERNAL_DELTA
    ):
        return PASS3_OUTCOME_NO_CANDIDATES

    return PASS3_OUTCOME_CANDIDATES_REJECTED


def _reject_sample_rows(trace: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    crs = trace.get("pass3_connectivity_reject_sample")
    if isinstance(crs, dict):
        rows.append({"source": "pass3_connectivity_reject_sample", **dict(crs)})
    diag = trace.get("p3e3_candidate_connectivity_reject_diagnostics") or trace.get(
        "p3e3_guarded_post_swap_connectivity_reject_diagnostics"
    )
    if isinstance(diag, dict) and diag:
        rows.append({"source": "p3e3_connectivity", **dict(diag)})
    return rows[:_MAX_SAMPLE_ROWS]


def enrich_pass3_trace_zero_gain_telemetry(trace: dict[str, Any]) -> None:
    """Mutates ``trace`` with Pass3 zero-gain / reject telemetry (best-effort, trace-only)."""

    reject_by = aggregate_pass3_reject_by_reason(trace)
    trace["pass3_reject_by_reason"] = reject_by

    outcome = classify_pass3_zero_gain_outcome(trace)
    trace["pass3_zero_gain_outcome"] = outcome

    n_out = int(trace.get("p3e2_outlet_count") or trace.get("pass3_routing_job_count") or 0)
    n_kinds = int(trace.get("p3f_candidate_kind_count") or 0)
    trace["pass3_candidate_route_count"] = max(n_out, n_kinds)

    raw_d = trace.get("p3f_internal_transport_delta")
    improved = False
    if raw_d is not None and int(raw_d) < 0:
        improved = True
    if bool(trace.get("p3e2_shadow_would_commit")):
        improved = True
    trace["pass3_candidate_improved_count"] = 1 if improved else 0

    best_delta: int | None = None
    if raw_d is not None:
        v = int(raw_d)
        if v < 0:
            best_delta = v
    trace["pass3_best_candidate_delta"] = best_delta

    best_rej: str | None = None
    if (
        best_delta is not None
        and best_delta < 0
        and not bool(trace.get("p3f_committed"))
        and not bool(trace.get("p3e3_guarded_commit_committed"))
    ):
        rr = trace.get("p3f_rejected_reason_raw")
        if isinstance(rr, str) and rr.strip():
            best_rej = bucket_for_p3e3_reason(rr) or rr
    trace["pass3_best_candidate_rejected_reason"] = best_rej

    gk = trace.get("pass3_transport_kind")
    if isinstance(gk, str) and gk:
        job_n = int(trace.get("pass3_routing_job_count") or n_out or 0)
        trace["pass3_goal_set_count_by_kind"] = {gk: job_n}
    else:
        trace["pass3_goal_set_count_by_kind"] = {}

    sm: dict[str, int] = {}
    for k in ("p3e2_lex_search_mode", "p3f_replacement_search_mode"):
        v = trace.get(k)
        if isinstance(v, str) and v.strip():
            sm[v] = int(sm.get(v, 0)) + 1
    trace["pass3_search_mode_counts"] = sm

    trace["pass3_reject_sample_rows"] = _reject_sample_rows(trace)

    total = int(sum(reject_by.values()))
    raw_rr = trace.get("p3f_rejected_reason_raw")
    raw_s = raw_rr if isinstance(raw_rr, str) else ""
    gd = trace.get("pass3_greedy_reject_detail")
    gds = gd if isinstance(gd, str) else ""
    trace["pass3_zero_gain_summary"] = (
        f"outcome={outcome};reject_total={total};" f"p3f_raw={raw_s};greedy_detail={gds}"
    )


__all__ = (
    "PASS3_OUTCOME_CANDIDATES_REJECTED",
    "PASS3_OUTCOME_IMPROVED",
    "PASS3_OUTCOME_NO_CANDIDATES",
    "PASS3_OUTCOME_SKIPPED",
    "PASS3_REJECT_BY_REASON_BUCKETS",
    "PASS3_ZERO_GAIN_TELEMETRY_KEYS",
    "aggregate_pass3_reject_by_reason",
    "classify_pass3_zero_gain_outcome",
    "enrich_pass3_trace_zero_gain_telemetry",
)
