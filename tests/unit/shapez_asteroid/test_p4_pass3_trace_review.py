"""Tests for scripts/debug/p4_pass3_trace_review.py (loaded via importlib; script is not a package)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "scripts" / "debug" / "p4_pass3_trace_review.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("p4_pass3_trace_review", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def tr():
    return _load_script()


def test_review_pass3_metrics_ok(tr) -> None:
    ss = {
        "pass3_rejected_reason": None,
        "p3f_rejected_reason": None,
        "before_internal_transport_count": 10,
        "after_internal_transport_count": 7,
        "pass3_internal_transport_saved": 3,
        "pass3_internal_transport_saved_implied": 3,
        "baseline_internal_transport_at_reclaim_entry": 7,
        "p4_reclaim_internal_transport_at_scan_entry": 7,
        "p4_reclaim_scan_entry_baseline_mismatch": False,
        "p4_reclaim_scan_preconditions": {
            "reclaimed_interior_transport_count": 3,
            "reclaim_anchor_candidate_count": 2,
        },
        "p4_reclaim_candidate_count": 1,
        "p4_reclaim_accepted_shadow_count": 1,
    }
    r = tr.review_solver_summary(ss)
    assert r["pass3_metrics_ok"] is True
    assert r["baseline_ok"] is True
    joined = "".join(r["branch_recommendations"])
    assert "pass3_reject_or_no_internal_delta_reclaimed_0" not in joined


def test_review_saved_gt_0_reclaimed_0_branch(tr) -> None:
    ss = {
        "pass3_rejected_reason": None,
        "p3f_rejected_reason": None,
        "before_internal_transport_count": 10,
        "after_internal_transport_count": 8,
        "pass3_internal_transport_saved": 2,
        "pass3_internal_transport_saved_implied": 2,
        "baseline_internal_transport_at_reclaim_entry": 8,
        "p4_reclaim_internal_transport_at_scan_entry": 8,
        "p4_reclaim_scan_entry_baseline_mismatch": False,
        "p4_reclaim_scan_preconditions": {
            "reclaimed_interior_transport_count": 0,
            "reclaim_anchor_candidate_count": 0,
        },
        "p4_reclaim_candidate_count": 0,
        "p4_reclaim_accepted_shadow_count": 0,
    }
    r = tr.review_solver_summary(ss)
    joined = " ".join(r["branch_recommendations"])
    assert "saved_gt_0_reclaimed_0" in joined


def test_review_pass3_metrics_ok_when_implied_key_missing(tr) -> None:
    ss = {
        "pass3_rejected_reason": None,
        "p3f_rejected_reason": None,
        "before_internal_transport_count": 10,
        "after_internal_transport_count": 7,
        "pass3_internal_transport_saved": 3,
        "baseline_internal_transport_at_reclaim_entry": 7,
        "p4_reclaim_internal_transport_at_scan_entry": 7,
        "p4_reclaim_scan_entry_baseline_mismatch": False,
        "p4_reclaim_scan_preconditions": {
            "reclaimed_interior_transport_count": 3,
            "reclaim_anchor_candidate_count": 1,
        },
        "p4_reclaim_candidate_count": 1,
        "p4_reclaim_accepted_shadow_count": 0,
    }
    r = tr.review_solver_summary(ss)
    assert r["pass3_metrics_ok"] is True
    assert r["pass3_internal_transport_saved_implied_effective"] == 3
    assert any("absent" in w for w in r["pass3_metric_warnings"])


def test_review_pass3_metrics_mismatch(tr) -> None:
    ss = {
        "pass3_rejected_reason": "rejected_by_gain_or_length",
        "p3f_rejected_reason": None,
        "before_internal_transport_count": 85,
        "after_internal_transport_count": 82,
        "pass3_internal_transport_saved": 0,
        "pass3_internal_transport_saved_implied": 3,
        "baseline_internal_transport_at_reclaim_entry": 85,
        "p4_reclaim_internal_transport_at_scan_entry": 85,
        "p4_reclaim_scan_entry_baseline_mismatch": False,
        "p4_reclaim_scan_preconditions": {
            "reclaimed_interior_transport_count": 0,
            "reclaim_anchor_candidate_count": 0,
        },
        "p4_reclaim_candidate_count": 0,
        "p4_reclaim_accepted_shadow_count": 0,
    }
    r = tr.review_solver_summary(ss)
    assert r["pass3_metrics_ok"] is False
    assert any("pass3_internal_transport_saved" in e for e in r["pass3_metric_errors"])
    assert r["branch_recommendations"][0].startswith("pass3_metrics_fail")


def test_last_solver_summary_ndjson(tmp_path, tr) -> None:
    p = tmp_path / "t.ndjson"
    row = {
        "kind": "trace",
        "message": "solver_summary",
        "data": {"solver_summary": {"run_id": "x"}},
    }
    p.write_text(json.dumps(row) + "\n", encoding="utf-8")
    last = tr.last_solver_summary_ndjson(p)
    assert last is not None
    assert last[0] == 1
    assert last[1]["run_id"] == "x"


def test_main_missing_file(tr, capsys) -> None:
    assert tr.main(["--ndjson", str(_REPO / "nonexistent_file.ndjson")]) == 1


def test_main_no_summary(tr, tmp_path, capsys) -> None:
    p = tmp_path / "empty.ndjson"
    p.write_text("{}\n", encoding="utf-8")
    assert tr.main(["--ndjson", str(p)]) == 1
