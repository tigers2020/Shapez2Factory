"""T5: ``solver_summary`` STEP4 failure aggregates (in-memory only)."""

from __future__ import annotations

import json

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    emit_solver_summary_once,
    trace_run_id_current,
    trace_run_scope,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.step4_route_failure_solver_summary import (  # noqa: E501
    build_step4_route_failure_aggregate_for_solver_summary,
    empty_step4_route_failure_aggregate_for_solver_summary,
)
from scripts.debug.t7_step4_ndjson_contracts import failure_detail_count_contract


def test_empty_aggregate_is_deterministic_zero() -> None:
    z = empty_step4_route_failure_aggregate_for_solver_summary()
    z2 = build_step4_route_failure_aggregate_for_solver_summary(())
    assert z == z2
    assert z["step4_failed_placement_ids"] == []
    assert z["step4_failure_details_count"] == 0
    assert z["step4_failure_attempt_detail_count"] == 0
    assert z["step4_failed_placement_count"] == 0
    assert z["step4_route_failure_category_counts"] == {}
    assert z["step4_rolled_back_failure_count"] == 0
    assert z["step4_quarantined_failure_count"] == 0


def test_aggregate_histograms_match_detail_rows() -> None:
    det = {
        "last_error": "no_route",
        "frontier_stop_reason": "exhausted",
        "search_mode": "goal_cells_union_legacy",
        "reachable_goal_count": 0,
        "search_budget_exhausted": False,
        "rolled_back": True,
        "quarantined": True,
        "transport_kind": "shape_belt",
        "step4_failure_category": "stub_isolated",
        "routing_failure_detail": {
            "step4_failure_category": "stub_isolated",
            "reachable_goal_count": 0,
            "search_budget_exhausted": False,
            "rolled_back": True,
            "quarantined": True,
        },
    }
    rows = [
        {
            "extractor_id": "p2-000001",
            "transport_kind": "shape_belt",
            "step4_route_failure_detail": det,
        }
    ]
    agg = build_step4_route_failure_aggregate_for_solver_summary(rows)
    assert agg["step4_failed_placement_ids"] == ["p2-000001"]
    assert agg["step4_failure_attempt_detail_count"] == 1
    assert agg["step4_failure_details_count"] == 1
    assert agg["step4_failed_placement_count"] == 1
    assert agg["step4_route_failure_category_counts"] == {"stub_isolated": 1}
    assert agg["step4_route_failure_last_error_counts"] == {"no_route": 1}
    assert agg["step4_route_failure_frontier_stop_reason_counts"] == {"exhausted": 1}
    assert agg["step4_search_mode_counts"] == {"goal_cells_union_legacy": 1}
    assert agg["step4_failure_transport_kind_counts"] == {"shape_belt": 1}
    assert agg["step4_reachable_goal_zero_count"] == 1
    assert agg["step4_search_budget_exhausted_count"] == 0
    assert agg["step4_rolled_back_failure_count"] == 1
    assert agg["step4_quarantined_failure_count"] == 1


def test_duplicate_placement_rows_increment_attempt_not_unique_count() -> None:
    det = {"last_error": "no_route", "step4_failure_category": "unknown"}
    rows = [
        {"extractor_id": "p2-000001", "step4_route_failure_detail": det},
        {"extractor_id": "p2-000001", "step4_route_failure_detail": dict(det)},
    ]
    agg = build_step4_route_failure_aggregate_for_solver_summary(rows)
    assert agg["step4_failure_attempt_detail_count"] == 2
    assert agg["step4_failure_details_count"] == 2
    assert agg["step4_failed_placement_count"] == 1
    assert agg["step4_failed_placement_ids"] == ["p2-000001"]
    assert agg["step4_route_failure_last_error_counts"] == {"no_route": 2}


def test_summary_detail_count_contract_uses_final_reentry_rows() -> None:
    fail_details = [
        {"placement_id": "p1-000001", "step4_reentry_index": 0},
        {"placement_id": "p1-000001", "step4_reentry_index": 1},
    ]
    contract = failure_detail_count_contract(
        fail_details=fail_details,
        solver_summary={"step4_failure_details_count": 1},
        step4_completed_data={"step4_reentry_index": 1},
    )
    assert contract == {
        "summary_count": 1,
        "raw_detail_count": 2,
        "final_reentry_index": 1,
        "final_reentry_detail_count": 1,
        "matches_final_reentry": True,
    }


def test_summary_detail_count_contract_flags_final_reentry_mismatch() -> None:
    contract = failure_detail_count_contract(
        fail_details=[{"placement_id": "p1-000001", "step4_reentry_index": 0}],
        solver_summary={"step4_failure_details_count": 1},
        step4_completed_data={"step4_reentry_index": 1},
    )
    assert contract["raw_detail_count"] == 1
    assert contract["final_reentry_detail_count"] == 0
    assert contract["matches_final_reentry"] is False


def test_emit_solver_summary_writes_debug_ndjson_when_algo_debug_on(
    tmp_path, monkeypatch, settings
) -> None:
    settings.BASE_DIR = tmp_path
    monkeypatch.setenv("SHAPEZ_SOLVER_ALGO_DEBUG", "1")
    with trace_run_scope():
        rid = trace_run_id_current()
        assert rid is not None
        assert emit_solver_summary_once(
            "test.emit",
            {"run_id": rid, "return_reason": "ok", "step4_routing_failure_count": 0},
        )
        assert not emit_solver_summary_once("test.emit", {"run_id": rid, "dup": True})
    dbg = tmp_path / "var" / "asteroid_mining_layout_debug" / f"{rid}.ndjson"
    text = dbg.read_text(encoding="utf-8").strip().splitlines()
    actions = [json.loads(line) for line in text if line.strip()]
    summaries = [a for a in actions if a.get("action") == "solver_summary"]
    assert len(summaries) == 1
    assert summaries[0]["data"]["solver_summary"]["return_reason"] == "ok"
