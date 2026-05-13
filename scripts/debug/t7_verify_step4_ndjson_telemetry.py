#!/usr/bin/env python3
"""T7 one-shot: run traced solver (partial STEP4) and verify ``latest.ndjson`` (debug stream).

Usage (repo root, Windows-friendly):
  set SHAPEZ_SOLVER_ALGO_DEBUG=1
  python scripts/debug/t7_verify_step4_ndjson_telemetry.py
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from unittest.mock import patch

# -----------------------------------------------------------------------------
# Django bootstrap
# -----------------------------------------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["SHAPEZ_SOLVER_ALGO_DEBUG"] = "1"

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.test.utils import override_settings  # noqa: E402

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import (  # noqa: E402
    Coord,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (  # noqa: E402
    pass1_timeline_integration as p12_int,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (  # noqa: E402
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (  # noqa: E402
    step4 as step4_stage,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (  # noqa: E402
    step4_merge_routing as step4_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (  # noqa: E402
    final_validation as finval,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import (  # noqa: E402
    build_map_timeline,
)

REQUIRED_DETAIL_KEYS: tuple[str, ...] = (
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
    "margin_goals_in_active_goal_cells_count",
    "active_goal_cells_count",
    "reachable_goal_count",
    "reachable_existing_trunk_count",
    "reachable_exterior_margin_count",
    "candidate_expanded_nodes",
    "expanded_nodes",
    "search_mode",
    "goal_ordering_mode",
    "fallback_reason",
    "search_budget_exhausted",
    "frontier_stop_reason",
    "last_error",
    "replacement_search_exhausted",
    "quarantined",
    "rolled_back",
    "step4_failure_category",
    "step4_failure_classification",
)

REQUIRED_SUMMARY_KEYS: tuple[str, ...] = (
    "step4_complete_routing_success",
    "step4_committed",
    "step4_routing_failure_count",
    "step4_failed_placement_ids",
    "step4_failure_details_count",
    "step4_route_failure_category_counts",
    "step4_route_failure_last_error_counts",
    "step4_route_failure_frontier_stop_reason_counts",
    "step4_search_mode_counts",
    "step4_failure_transport_kind_counts",
    "step4_reachable_goal_zero_count",
    "step4_search_budget_exhausted_count",
    "step4_rolled_back_failure_count",
    "step4_quarantined_failure_count",
)

ALLOWED_CATEGORIES: frozenset[str] = frozenset(
    {
        "geometry_cage",
        "protected_corridor_ring",
        "merge_starvation",
        "route_zone_overblocking",
        "search_budget_exhausted",
        "no_same_kind_trunk",
        "stub_isolated",
        "orphan_merge_forbidden",
        "goal_starvation",
        "mixed_transport_contamination",
        "unknown",
    }
)


def _decoded_shape_miners_with_belt_escape() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for x in range(10, 13):
        entries.append({"X": x, "Y": 0, "T": "Layout_ShapeMiner"})
    for x in range(13, 30):
        entries.append({"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0})
    return {"BP": {"Entries": entries}}


def main() -> int:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = finval.external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = p12_int.integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    jobs = step4_mod._collect_routing_jobs(dict(finval.cells_dict_from_mining_map(m2)))
    if not jobs:
        print("FAIL: no routing jobs after Pass12 integration")
        return 5
    _ext_cell, fail_stub, _tk, fail_pid = jobs[-1]
    if not isinstance(fail_pid, str) or not fail_pid:
        print("FAIL: last job missing placement_id")
        return 6

    real = step4_mod._dijkstra_route

    def wrapped(stub_cell: Coord, *args: Any, **kwargs: Any) -> tuple[Coord, ...] | None:
        if stub_cell == fail_stub:
            return None
        return real(stub_cell, *args, **kwargs)

    real_run_step4 = step4_mod.run_step4_merge_aware_routing

    def forced_step4(*args: Any, **kwargs: Any) -> Any:
        kwargs["force_route_attempt_placement_ids"] = frozenset({fail_pid})
        return real_run_step4(*args, **kwargs)

    with (
        patch.object(step4_mod, "_dijkstra_route", new=wrapped),
        patch.object(step4_stage, "run_step4_merge_aware_routing", new=forced_step4),
        override_settings(SHAPEZ_MINING_ASSERT_STEP9_ROUTING_STATE=True),
    ):
        build_solver_timeline(decoded)

    latest = Path(settings.BASE_DIR) / "var" / "asteroid_mining_layout_debug" / "latest.ndjson"
    if not latest.is_file():
        print("FAIL: latest.ndjson missing at", latest)
        return 2

    lines = [ln for ln in latest.read_text(encoding="utf-8").splitlines() if ln.strip()]
    rows: list[dict[str, Any]] = []
    for ln in lines:
        try:
            rows.append(json.loads(ln))
        except json.JSONDecodeError as e:
            print("FAIL: invalid JSON line:", e)
            return 3

    actions = [r.get("action") for r in rows if r.get("kind") == "action"]
    action_set = frozenset(a for a in actions if isinstance(a, str))

    required_actions = (
        "run_start",
        "step4_route_failure_detail",
        "step4_completed",
        "pass3_eligibility_checked",
        "final_validation_completed",
        "pipeline_return",
        "solver_summary",
        "run_end",
    )
    print("NDJSON path:", latest)
    print("total_rows", len(rows))
    print("--- action presence ---")
    for a in required_actions:
        ok = a in action_set
        print(f"  {a}: {'PASS' if ok else 'FAIL'}")

    fail_details: list[dict[str, Any]] = []
    step4_completed_data: dict[str, Any] | None = None
    solver_summary: dict[str, Any] | None = None
    for r in rows:
        if r.get("kind") != "action":
            continue
        if r.get("action") == "step4_route_failure_detail":
            d = (r.get("data") or {}).get("step4_route_failure_detail")
            if isinstance(d, dict):
                fail_details.append(d)
        elif r.get("action") == "step4_completed":
            step4_completed_data = dict(r.get("data") or {})
        elif r.get("action") == "solver_summary":
            ss = (r.get("data") or {}).get("solver_summary")
            if isinstance(ss, dict):
                solver_summary = ss

    print("failure_detail_events", len(fail_details))
    if "step4_route_failure_detail" in action_set and not fail_details:
        print("FAIL: step4_route_failure_detail action present but no parsable detail dicts")
        return 4

    detail_group = "PASS"
    for i, det in enumerate(fail_details):
        missing = [k for k in REQUIRED_DETAIL_KEYS if k not in det]
        if missing:
            print(f"FAIL detail[{i}] missing keys:", missing)
            detail_group = "FAIL"
        if "commit_reason" in det:
            print(f"FAIL detail[{i}] must not contain commit_reason")
            detail_group = "FAIL"
        cat = det.get("step4_failure_category")
        if str(cat) not in ALLOWED_CATEGORIES:
            print(f"FAIL detail[{i}] bad category:", cat)
            detail_group = "FAIL"
        clf = det.get("step4_failure_classification")
        if not isinstance(clf, dict):
            print(f"FAIL detail[{i}] classification not object")
            detail_group = "FAIL"
        fs = det.get("frontier_stop_reason")
        sbe = det.get("search_budget_exhausted")
        le = str(det.get("last_error") or "")
        if fs in ("exhausted", None) and le.endswith("exhausted") or le == "no_route_exhausted":
            if sbe is True:
                print(f"WARN detail[{i}] budget flag true with exhausted-ish last_error={le!r}")
        if sbe is True and fs == "exhausted":
            print(f"FAIL detail[{i}] search_budget_exhausted with frontier exhausted")
            detail_group = "FAIL"

    print("detail_key_group", detail_group)

    summary_group = "PASS"
    if not isinstance(solver_summary, dict):
        print("FAIL: no solver_summary dict on wire")
        summary_group = "FAIL"
    else:
        miss = [k for k in REQUIRED_SUMMARY_KEYS if k not in solver_summary]
        if miss:
            print("FAIL solver_summary missing:", miss)
            summary_group = "FAIL"

    print("summary_key_group", summary_group)

    # Category / count summary
    cats: Counter[str] = Counter()
    last_err: Counter[str] = Counter()
    frontier: Counter[str] = Counter()
    rgs: Counter[int] = Counter()
    rgc: Counter[int] = Counter()
    pids: set[str] = set()
    for det in fail_details:
        cats[str(det.get("step4_failure_category") or "")] += 1
        last_err[str(det.get("last_error") or "")] += 1
        frontier[str(det.get("frontier_stop_reason") or "")] += 1
        try:
            rgs[int(det.get("route_goal_set_size") or 0)] += 1
        except (TypeError, ValueError):
            rgs[-1] += 1
        try:
            rgc[int(det.get("reachable_goal_count") or 0)] += 1
        except (TypeError, ValueError):
            rgc[-1] += 1
        pid = det.get("placement_id") or det.get("extractor_id")
        if isinstance(pid, str) and pid:
            pids.add(pid)

    print("--- distributions ---")
    print("unique_failed_placement_ids", sorted(pids))
    print("step4_failure_category_counts", dict(sorted(cats.items())))
    print("last_error_counts", dict(sorted(last_err.items())))
    print("frontier_stop_reason_counts", dict(sorted(frontier.items())))
    print("route_goal_set_size_distribution", dict(sorted(rgs.items())))
    print("reachable_goal_count_distribution", dict(sorted(rgc.items())))

    if isinstance(solver_summary, dict) and isinstance(step4_completed_data, dict):
        rb_completed = set(
            str(x) for x in (step4_completed_data.get("rolled_back_placement_ids") or []) if x
        )
        rb_detail = {
            str(det.get("placement_id") or "")
            for det in fail_details
            if det.get("rolled_back")
        }
        rb_detail.discard("")
        if rb_detail - rb_completed:
            diff = rb_detail - rb_completed
            print("WARN: rolled_back detail ids not subset of step4_completed:", diff)

        sfc = int(solver_summary.get("step4_failure_details_count") or 0)
        if sfc != len(fail_details):
            print(
                "WARN: solver_summary step4_failure_details_count != NDJSON detail rows",
                sfc,
                len(fail_details),
            )

    fv = None
    if isinstance(solver_summary, dict):
        fv = solver_summary.get("final_validation")
    if isinstance(fv, dict):
        print("final_validation.geometry_valid", fv.get("geometry_valid"))
        print("final_validation.connectivity_valid", fv.get("connectivity_valid"))
    pass3_elig = next(
        (r.get("data") for r in rows if r.get("action") == "pass3_eligibility_checked"),
        None,
    )
    if isinstance(pass3_elig, dict):
        print("pass3_eligibility.eligible", pass3_elig.get("eligible"))
        print("pass3_eligibility.skip_reason", pass3_elig.get("skip_reason"))

    p4c = next((r.get("data") for r in rows if r.get("action") == "p4_reclaim_completed"), None)
    if isinstance(p4c, dict):
        print("p4_reclaim_completed.enabled", p4c.get("enabled"))
        print("p4_reclaim_completed.skip_reason", p4c.get("skip_reason"))
    else:
        print("p4_reclaim_completed: (no action row — may be skipped on partial STEP4)")

    routing_root = Path("django_apps/shapez_asteroid/services/asteroid_mining_layout/step4")
    algo_ok = True
    for fname in ("step4_dijkstra.py", "step4_merge_routing.py", "step4_routing_permission.py"):
        t = (routing_root / fname).read_text(encoding="utf-8").lower()
        if "solver_summary" in t or "ndjson" in t:
            print("FAIL algorithm boundary:", fname)
            algo_ok = False
    print("algorithm_static_scan", "PASS" if algo_ok else "FAIL")

    ok = (
        all(a in action_set for a in required_actions)
        and detail_group == "PASS"
        and summary_group == "PASS"
        and bool(fail_details)
    )
    if not fail_details:
        print(
            "NOTE: 10-failure scenario not reproduced; this fixture yields",
            len(fail_details),
            "NDJSON detail rows.",
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
