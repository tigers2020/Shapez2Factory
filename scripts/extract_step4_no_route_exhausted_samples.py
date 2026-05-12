#!/usr/bin/env python3
"""Extract representative STEP4 ``no_route_exhausted`` rows from mining-layout NDJSON.

Reads ``var/asteroid_mining_layout_debug/latest.ndjson`` by default (repo-relative).
Diagnostics only; does not import Django apps.

Usage:
  python scripts/extract_step4_no_route_exhausted_samples.py
  python scripts/extract_step4_no_route_exhausted_samples.py --path path/to/run.ndjson --limit 5
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _walk(obj: Any, depth: int = 0) -> list[Any]:
    """Collect dict/list nodes (shallow walk for finding routing_failures)."""
    if depth > 14:
        return []
    out: list[Any] = []
    if isinstance(obj, dict):
        out.append(obj)
        for v in obj.values():
            out.extend(_walk(v, depth + 1))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_walk(v, depth + 1))
    return out


def _extract_diag(row: dict[str, Any]) -> dict[str, Any] | None:
    d = row.get("step4_route_failure_diagnostic")
    if isinstance(d, dict):
        return d
    det = row.get("step4_route_failure_detail")
    if isinstance(det, dict):
        d2 = det.get("step4_route_failure_diagnostic")
        if isinstance(d2, dict):
            return d2
    return None


def _extract_detail(row: dict[str, Any]) -> dict[str, Any]:
    det = row.get("step4_route_failure_detail")
    return det if isinstance(det, dict) else {}


def _breaker_category(diag: dict[str, Any], detail: dict[str, Any]) -> str:
    """Mirror step4_route_failure_diagnostic._row_breaker_category_no_route_exhausted (subset)."""

    def stub_neighbors_all_hard_protected() -> bool:
        near = detail.get("blocked_reason_near_stub")
        if not isinstance(near, list) or len(near) < 1:
            return False
        reasons = [str(x.get("reason", "")) for x in near if isinstance(x, dict)]
        return bool(reasons) and all(r == "hard_protected" for r in reasons)

    def stub_neighbors_geometry_blocked() -> bool:
        near = detail.get("blocked_reason_near_stub")
        if not isinstance(near, list) or len(near) < 1:
            return False
        bad = frozenset({"blocked", "step_cost_none"})
        reasons = [str(x.get("reason", "")) for x in near if isinstance(x, dict)]
        return bool(reasons) and all(r in bad for r in reasons)

    ext = int(diag.get("exterior_goal_count") or 0)
    et = int(diag.get("existing_trunk_goal_count") or 0)
    exn = diag.get("expanded_nodes")
    exn_i = exn if type(exn) is int and not isinstance(exn, bool) else None

    if stub_neighbors_all_hard_protected():
        return "hard_protected_ring"
    if stub_neighbors_geometry_blocked():
        return "stub_local_geometry_or_corridor"
    if ext == 0 and et > 0:
        return "trunk_union_goals_unreachable_from_stub"
    if exn_i is not None and exn_i >= 20:
        return "wide_search_exhausted"
    if exn_i is not None and exn_i <= 7:
        return "narrow_search_exhausted"
    return "other_no_route_exhausted"


def _classifier_inputs(diag: dict[str, Any], detail: dict[str, Any]) -> dict[str, Any]:
    nh = _resolved_nearest_hops(diag, detail)
    return {
        "goal_count": diag.get("goal_count"),
        "exterior_goal_count": diag.get("exterior_goal_count"),
        "existing_trunk_goal_count": diag.get("existing_trunk_goal_count"),
        "stub_cell_role_ok": diag.get("stub_cell_role_ok"),
        "nearest_transport_hops": nh,
        "stop_reason": diag.get("stop_reason"),
        "last_error": detail.get("last_error"),
        "route_length_ratio_exceeded": diag.get("route_length_ratio_exceeded"),
    }


def _resolved_nearest_hops(diag: dict[str, Any], detail: dict[str, Any]) -> int | None:
    """Prefer diagnostic classifier hops; fall back to detail distance (matches breakdown hist)."""

    ci = diag.get("classifier_inputs")
    if isinstance(ci, dict):
        h = ci.get("nearest_transport_hops")
        if type(h) is int and not isinstance(h, bool):
            return h
    bl = diag.get("baseline_route_length")
    if type(bl) is int and not isinstance(bl, bool):
        return bl
    d = detail.get("nearest_existing_transport_distance")
    if type(d) is int and not isinstance(d, bool):
        return d
    return None


def _sample_row(row: dict[str, Any]) -> dict[str, Any]:
    diag = _extract_diag(row) or {}
    detail = _extract_detail(row)
    nh = _resolved_nearest_hops(diag, detail)
    pid = diag.get("placement_id") or row.get("placement_id") or detail.get("placement_id")
    fr = diag.get("failure_reason")
    breaker = _breaker_category(diag, detail) if fr == "no_route_exhausted" else None
    return {
        "placement_id": pid,
        "placement_pass": diag.get("placement_pass") or row.get("placement_pass"),
        "extractor_cell": diag.get("extractor_cell") or detail.get("extractor_cell"),
        "stub_cell": diag.get("stub_cell") or detail.get("stub_cell"),
        "transport_kind": diag.get("transport_kind") or row.get("transport_kind"),
        "failure_reason": diag.get("failure_reason"),
        "breaker_category": breaker,
        "nearest_transport_hops": nh,
        "goal_count": diag.get("goal_count"),
        "exterior_goal_count": diag.get("exterior_goal_count"),
        "existing_trunk_goal_count": diag.get("existing_trunk_goal_count"),
        "expanded_nodes": diag.get("expanded_nodes"),
        "blocked_reason_near_stub": detail.get("blocked_reason_near_stub"),
        "stub_role": diag.get("stub_role"),
        "expected_stub_role": diag.get("expected_stub_role") or row.get("expected_stub_role"),
        "classifier_inputs": _classifier_inputs(diag, detail),
    }


def collect_no_route_exhausted_rows(
    ndjson_path: Path,
    *,
    dedupe_placement_id: bool = True,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    text = ndjson_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "no_route_exhausted" not in line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        data = obj.get("data")
        roots: list[Any] = [obj]
        if isinstance(data, dict):
            roots.append(data)
        for root in roots:
            for node in _walk(root):
                if not isinstance(node, dict):
                    continue
                if "routing_failures" in node and isinstance(node["routing_failures"], list):
                    for rf in node["routing_failures"]:
                        if not isinstance(rf, dict):
                            continue
                        d = _extract_diag(rf)
                        if d and d.get("failure_reason") == "no_route_exhausted":
                            pid = d.get("placement_id")
                            if dedupe_placement_id:
                                key = str(pid) if pid is not None else ""
                                if key and key in seen:
                                    continue
                                if key:
                                    seen.add(key)
                            rows.append(rf)
    return rows


def representative_subset(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Prefer one row per distinct breaker_category, then fill by order."""
    keyed: list[tuple[str, dict[str, Any]]] = []
    for r in rows:
        s = _sample_row(r)
        cat = s.get("breaker_category") or "unknown"
        keyed.append((cat, r))
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for cat, r in keyed:
        by_cat.setdefault(cat, []).append(r)
    out: list[dict[str, Any]] = []
    cats = sorted(by_cat.keys(), key=lambda c: (-len(by_cat[c]), c))
    for cat in cats:
        if len(out) >= limit:
            break
        out.append(by_cat[cat][0])
    i = 0
    while len(out) < limit and i < len(rows):
        if rows[i] not in out:
            out.append(rows[i])
        i += 1
    return out[:limit]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--path",
        type=Path,
        default=_repo_root() / "var" / "asteroid_mining_layout_debug" / "latest.ndjson",
        help="NDJSON trace file",
    )
    ap.add_argument("--limit", type=int, default=5, help="Max samples (default 5)")
    ap.add_argument(
        "--no-dedupe",
        action="store_true",
        help="Keep duplicate placement_id rows (NDJSON may log routing_failures twice)",
    )
    args = ap.parse_args()
    path: Path = args.path
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    rows = collect_no_route_exhausted_rows(path, dedupe_placement_id=not args.no_dedupe)
    print(f"file: {path}")
    print(f"no_route_exhausted routing_failures rows: {len(rows)}")
    cats: Counter[str] = Counter()
    for r in rows:
        s = _sample_row(r)
        cats[str(s.get("breaker_category"))] += 1
    print("breaker_category histogram:", dict(cats))
    subset = representative_subset(rows, max(1, args.limit))
    for j, r in enumerate(subset, start=1):
        print(f"\n--- sample {j} ---")
        print(json.dumps(_sample_row(r), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
