#!/usr/bin/env python3
"""Extract Pass3/P4 trace fields from mining-layout NDJSON and apply the P4 review branch table.

Reads the last ``solver_summary`` object in an NDJSON file (default:
``var/asteroid_mining_layout_debug/latest.ndjson`` relative to repo root).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any


def _as_int(v: Any) -> int | None:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return None


def _solver_summary_from_record(obj: dict[str, Any]) -> dict[str, Any] | None:
    if obj.get("kind") != "trace":
        return None
    if obj.get("message") != "solver_summary":
        return None
    data = obj.get("data")
    if not isinstance(data, dict):
        return None
    ss = data.get("solver_summary")
    return ss if isinstance(ss, dict) else None


def iter_solver_summaries_ndjson(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield (1-based line_no, solver_summary dict) for each matching NDJSON line."""

    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            ss = _solver_summary_from_record(obj)
            if ss is not None:
                yield i, ss


def last_solver_summary_ndjson(path: Path) -> tuple[int, dict[str, Any]] | None:
    last: tuple[int, dict[str, Any]] | None = None
    for item in iter_solver_summaries_ndjson(path):
        last = item
    return last


def review_solver_summary(ss: dict[str, Any]) -> dict[str, Any]:
    """Return structured checks and branch recommendations (no I/O)."""

    p3_rej = ss.get("pass3_rejected_reason")
    p3f_rej = ss.get("p3f_rejected_reason")
    before = _as_int(ss.get("before_internal_transport_count"))
    after = _as_int(ss.get("after_internal_transport_count"))
    saved = _as_int(ss.get("pass3_internal_transport_saved"))
    implied = _as_int(ss.get("pass3_internal_transport_saved_implied"))

    implied_calc: int | None = None
    if before is not None and after is not None:
        implied_calc = max(0, before - after)

    pass3_metric_warnings: list[str] = []
    implied_eff = implied
    if implied_eff is None and implied_calc is not None:
        implied_eff = implied_calc
        pass3_metric_warnings.append(
            "pass3_internal_transport_saved_implied absent; using max(0, before-after) for checks"
        )

    pass3_metrics_ok: bool | None = None
    pass3_metric_errors: list[str] = []
    if before is None or after is None or saved is None:
        pass3_metrics_ok = None
        if before is None:
            pass3_metric_errors.append("missing before_internal_transport_count")
        if after is None:
            pass3_metric_errors.append("missing after_internal_transport_count")
        if saved is None:
            pass3_metric_errors.append("missing pass3_internal_transport_saved")
    elif implied_calc is None:
        pass3_metrics_ok = None
        pass3_metric_errors.append("cannot derive max(0, before-after)")
    else:
        if implied is not None and implied != implied_calc:
            pass3_metric_errors.append(
                f"pass3_internal_transport_saved_implied ({implied}) != "
                f"max(0, before-after) ({implied_calc})"
            )
        if implied_eff is not None and saved != implied_eff:
            pass3_metric_errors.append(
                f"pass3_internal_transport_saved ({saved}) != "
                f"pass3_internal_transport_saved_implied ({implied_eff})"
            )
        pass3_metrics_ok = not pass3_metric_errors

    baseline = _as_int(ss.get("baseline_internal_transport_at_reclaim_entry"))
    scan_entry = _as_int(ss.get("p4_reclaim_internal_transport_at_scan_entry"))
    mismatch = ss.get("p4_reclaim_scan_entry_baseline_mismatch")
    baseline_ok: bool | None
    baseline_errors: list[str] = []
    if mismatch is True:
        baseline_ok = False
        baseline_errors.append("p4_reclaim_scan_entry_baseline_mismatch is True")
    elif mismatch is False:
        if baseline is not None and scan_entry is not None and baseline != scan_entry:
            baseline_ok = False
            baseline_errors.append(
                f"baseline_internal_transport_at_reclaim_entry ({baseline}) != "
                f"p4_reclaim_internal_transport_at_scan_entry ({scan_entry})"
            )
        else:
            baseline_ok = True
    else:
        if baseline is not None and scan_entry is not None and baseline != scan_entry:
            baseline_ok = False
            baseline_errors.append(
                "p4_reclaim_scan_entry_baseline_mismatch absent but baseline != scan_entry"
            )
        elif baseline is None or scan_entry is None:
            baseline_ok = None
            if baseline is None:
                baseline_errors.append("missing baseline_internal_transport_at_reclaim_entry")
            if scan_entry is None:
                baseline_errors.append("missing p4_reclaim_internal_transport_at_scan_entry")
        else:
            baseline_ok = True

    pre = ss.get("p4_reclaim_scan_preconditions")
    pre_d: dict[str, Any] = pre if isinstance(pre, dict) else {}
    reclaimed = _as_int(pre_d.get("reclaimed_interior_transport_count"))
    anchor = _as_int(pre_d.get("reclaim_anchor_candidate_count"))
    candidate = _as_int(ss.get("p4_reclaim_candidate_count"))
    accepted = _as_int(ss.get("p4_reclaim_accepted_shadow_count"))

    committed_reclaimed_transport = bool(saved and saved > 0)

    branches: list[str] = []
    if saved is not None and reclaimed is not None and saved > 0 and reclaimed == 0:
        branches.append(
            "saved_gt_0_reclaimed_0: investigate reclaim_map_ops or before/after map handoff"
        )
    elif reclaimed is not None and reclaimed == 0:
        pass3_idle = bool(p3_rej) or (before is not None and after is not None and before == after)
        if pass3_idle:
            branches.append(
                "pass3_reject_or_no_internal_delta_reclaimed_0: P4 idle OK; "
                "next Pass3 connectivity/gain (route A)"
            )
            if p3f_rej == "rejected_by_connectivity":
                branches.append("p3f_rejected_reason=rejected_by_connectivity reinforces route A")
        elif before is not None and after is not None and before != after and saved == 0:
            branches.append(
                "internal_counts_differ_but_saved_0: ambiguous — verify Pass3 commit vs "
                "summary field semantics before blaming P4"
            )
    if reclaimed is not None and anchor is not None and reclaimed > 0 and anchor == 0:
        branches.append(
            "reclaimed_gt_0_anchor_0: scan geometry (mineable ∩ reclaimed, protected, final route)"
        )
    if anchor is not None and candidate is not None and anchor > 0 and candidate == 0:
        branches.append(
            "anchor_gt_0_candidate_0: bundle / stub / extension / incremental routing (route B)"
        )
    if candidate is not None and accepted is not None and candidate > 0 and accepted == 0:
        branches.append(
            "candidate_gt_0_accepted_0: P4 policy (gain_ratio, length_ratio, budget, corridor)"
        )

    if pass3_metrics_ok is False:
        branches.insert(
            0,
            "pass3_metrics_fail: align pass3_internal_transport_saved with implied "
            "(or emit pass3_internal_transport_saved_implied in solver_summary)",
        )

    return {
        "pass3_rejected_reason": p3_rej,
        "p3f_rejected_reason": p3f_rej,
        "before_internal_transport_count": before,
        "after_internal_transport_count": after,
        "pass3_internal_transport_saved": saved,
        "pass3_internal_transport_saved_implied": implied,
        "pass3_internal_transport_saved_implied_effective": implied_eff,
        "implied_from_before_after": implied_calc,
        "pass3_metrics_ok": pass3_metrics_ok,
        "pass3_metric_errors": pass3_metric_errors,
        "pass3_metric_warnings": pass3_metric_warnings,
        "baseline_internal_transport_at_reclaim_entry": baseline,
        "p4_reclaim_internal_transport_at_scan_entry": scan_entry,
        "p4_reclaim_scan_entry_baseline_mismatch": mismatch,
        "baseline_ok": baseline_ok,
        "baseline_errors": baseline_errors,
        "p4_reclaim_scan_preconditions": pre_d or None,
        "p4_reclaim_candidate_count": candidate,
        "p4_reclaim_accepted_shadow_count": accepted,
        "committed_reclaimed_transport_saved_gt_0": committed_reclaimed_transport,
        "branch_recommendations": branches,
    }


def _print_report(path: Path, line_no: int | None, report: dict[str, Any]) -> None:
    print(f"NDJSON: {path}")
    if line_no is not None:
        print(f"solver_summary line: {line_no}")
    print()
    print("=== 1. Pass3 six metrics ===")
    for k in (
        "pass3_rejected_reason",
        "p3f_rejected_reason",
        "before_internal_transport_count",
        "after_internal_transport_count",
        "pass3_internal_transport_saved",
        "pass3_internal_transport_saved_implied",
        "implied_from_before_after",
    ):
        print(f"  {k}: {report.get(k)}")
    ok = report.get("pass3_metrics_ok")
    eff = report.get("pass3_internal_transport_saved_implied_effective")
    print(f"  pass3_internal_transport_saved_implied_effective: {eff}")
    print(f"  pass3_metrics_ok: {ok}")
    for w in report.get("pass3_metric_warnings") or []:
        print(f"  WARN: {w}")
    for err in report.get("pass3_metric_errors") or []:
        print(f"  ERROR: {err}")
    print()
    print("=== 2. P4 baseline handoff ===")
    for k in (
        "baseline_internal_transport_at_reclaim_entry",
        "p4_reclaim_internal_transport_at_scan_entry",
        "p4_reclaim_scan_entry_baseline_mismatch",
    ):
        print(f"  {k}: {report.get(k)}")
    print(f"  baseline_ok: {report.get('baseline_ok')}")
    for err in report.get("baseline_errors") or []:
        print(f"  ERROR: {err}")
    print()
    print("=== 3. P4 scan preconditions + candidates ===")
    print(f"  p4_reclaim_scan_preconditions: {report.get('p4_reclaim_scan_preconditions')}")
    print(f"  p4_reclaim_candidate_count: {report.get('p4_reclaim_candidate_count')}")
    print(f"  p4_reclaim_accepted_shadow_count: {report.get('p4_reclaim_accepted_shadow_count')}")
    print()
    print("=== Core question ===")
    print(
        "  Pass3 committed reclaimed transport (proxy: pass3_internal_transport_saved > 0): "
        f"{report.get('committed_reclaimed_transport_saved_gt_0')}"
    )
    print()
    print("=== Branch recommendations ===")
    br = report.get("branch_recommendations") or []
    if not br:
        print("  (none — no table row matched beyond generic review)")
    for b in br:
        print(f"  - {b}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _repo = Path(__file__).resolve().parents[1]
    default_ndjson = _repo / "var" / "asteroid_mining_layout_debug" / "latest.ndjson"
    parser.add_argument(
        "--ndjson",
        type=Path,
        default=default_ndjson,
        help="path to NDJSON (default: var/asteroid_mining_layout_debug/latest.ndjson under repo)",
    )
    args = parser.parse_args(argv)
    path: Path = args.ndjson
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1
    last = last_solver_summary_ndjson(path)
    if last is None:
        print(f"error: no solver_summary record in {path}", file=sys.stderr)
        return 1
    line_no, ss = last
    report = review_solver_summary(ss)
    _print_report(path, line_no, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
