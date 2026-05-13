"""Termination.degradation_causes 보강: success/partial_success + 품질 지표."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    DEGRADATION_CAUSE_EXTRACTOR_DROP_VS_MERGED_SEED,
    DEGRADATION_CAUSE_PASS2_EMPTY_GOAL_PROBE,
    DEGRADATION_CAUSE_PRESERVE_MISSING_STUB_DROP,
    OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    SOLVER_TERMINATION_SUCCESS,
    build_final_solver_output,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    step4_routing_skipped_result,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation_contracts import (  # noqa: E501
    FinalValidationReport,
)


def _empty_counts() -> dict[str, int]:
    return {"extractors": 0, "extensions": 0, "transport_cells": 0}


def test_success_tier_appends_degradation_causes_from_pass12_signals() -> None:
    """SUCCESS tier에도 extractor/preserve/pass2 질표를 ``degradation_causes``에 남긴다."""

    empty: list[dict[str, Any]] = []
    routing_state: dict[str, Any] = {"hard_protected_corridors": []}
    step4 = step4_routing_skipped_result(empty)
    good = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
        extractor_count=7,
        extension_count=0,
        transport_cell_count=0,
        transport_connectivity_ok=True,
    )
    pass12_stats: dict[str, Any] = {
        "pass12_merged_seed_miner_count": 10,
        "pass12_preserved_bundle_extractor_cells": 7,
        "pass12_preserved_missing_stub_drop_extractor_count": 0,
        "pass12_preserved_recovery_success_count": 0,
        "pass12_preserved_rotation_recovery_count": 0,
        "pass12_preserved_missing_stub_route_recovery_attempted_count": 0,
        "pass12_preserved_missing_stub_route_recovery_success_count": 0,
        "pass12_preserved_recovered_stub_samples": [],
        "pass12_preserved_unrecovered_stub_drop_samples": [],
        "pass2_probe_empty_goal_set_count": 2,
        "pass2_probe_last_goal_trace": {
            "final_goal_count": 3,
            "pass2_external_margin_diagnostic": {
                "universe_scan_cell_count": 9,
                "sampled_neighbor_coord_count": 0,
            },
        },
        "preserve_missing_stub_summary": {
            "drop_count": 1,
            "by_reason": {},
            "by_recoverability": {},
            "by_rejected_reason_subtype": {},
            "local_repack_candidate_count": 0,
        },
    }
    pass3_summary: dict[str, Any] = {
        "after_internal_transport_count": 0,
        "pass3_skipped": True,
        "pass3_committed": False,
    }
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize."
        "_validate_final_mining_layout",
        return_value=good,
    ):
        _out, summary = build_final_solver_output(
            run_id="deg-causes-success-tier",
            map_timeline=[{"mining_map": empty}, {"mining_map": empty}],
            map_after_pass1=empty,
            map_after_pass2=empty,
            map_after_routing=empty,
            map_final=empty,
            pass12_status_fields={},
            pass12_stats=pass12_stats,
            pass12_phase="test",
            pass12_skipped=True,
            pre_counts=_empty_counts(),
            post_pass2_counts=_empty_counts(),
            step4_result=step4,
            routing_state_summary=routing_state,
            post_step4_counts=_empty_counts(),
            unfinalized_placement_count=0,
            pass3_summary=pass3_summary,
            existing_layout_analysis=None,
            step_hash_step4=None,
            step_hash_pass3=None,
            step_hash_p4=None,
            solver_state_hash=None,
            replay_events=[],
            debug_location="tests.unit.shapez_asteroid.test_finalize_degradation_causes_success_tier",
        )

    assert summary["solver_termination"] == SOLVER_TERMINATION_SUCCESS
    term = summary["termination"]
    assert term["tier"] == "SUCCESS"
    dc = list(term["degradation_causes"])
    assert DEGRADATION_CAUSE_EXTRACTOR_DROP_VS_MERGED_SEED in dc
    assert DEGRADATION_CAUSE_PRESERVE_MISSING_STUB_DROP in dc
    assert DEGRADATION_CAUSE_PASS2_EMPTY_GOAL_PROBE in dc
    assert _out["termination"] == summary["termination"]
    assert summary["preserve_missing_stub_summary"]["drop_count"] == 1
    gtrace = summary.get("pass2_probe_last_goal_trace") or {}
    assert "pass2_external_margin_diagnostic" in gtrace
    md = gtrace["pass2_external_margin_diagnostic"] or {}
    assert int(md.get("universe_scan_cell_count")) == 9


def test_solver_summary_synthesizes_preserve_missing_stub_from_drop_details() -> None:
    """drop_extractor_count와 상세 행이 있으면 ``preserve_missing_stub_summary``를 재합성한다."""

    empty: list[dict[str, Any]] = []
    routing_state: dict[str, Any] = {"hard_protected_corridors": []}
    step4 = step4_routing_skipped_result(empty)
    good = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
        extractor_count=10,
        extension_count=0,
        transport_cell_count=0,
        transport_connectivity_ok=True,
    )
    pass12_stats: dict[str, Any] = {
        "pass12_merged_seed_miner_count": 10,
        "pass12_preserved_bundle_extractor_cells": 10,
        "pass12_preserved_missing_stub_drop_extractor_count": 2,
        "pass12_preserved_missing_stub_drop_details": [
            {
                "preserve_drop_reason": "NO_MATCHING_STUB",
                "recoverability_class": "NEAR_TRANSPORT",
                "preserve_stub_recovery": {"rejected_reason_subtype": "occupied_neighbor_ring"},
            },
            {
                "preserve_drop_reason": "NO_MATCHING_STUB",
                "recoverability_class": "NEAR_TRANSPORT",
                "preserve_stub_recovery": {},
            },
        ],
        "pass12_preserved_recovery_success_count": 0,
        "pass12_preserved_rotation_recovery_count": 0,
        "pass12_preserved_missing_stub_route_recovery_attempted_count": 0,
        "pass12_preserved_missing_stub_route_recovery_success_count": 0,
        "pass12_preserved_recovered_stub_samples": [],
        "pass12_preserved_unrecovered_stub_drop_samples": [],
        "pass2_probe_empty_goal_set_count": 0,
        "preserve_missing_stub_summary": {
            "drop_count": 0,
            "by_reason": {},
            "by_recoverability": {},
            "by_rejected_reason_subtype": {},
            "local_repack_candidate_count": 0,
        },
    }
    pass3_summary: dict[str, Any] = {
        "after_internal_transport_count": 0,
        "pass3_skipped": True,
        "pass3_committed": False,
    }
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize."
        "_validate_final_mining_layout",
        return_value=good,
    ):
        _, summary = build_final_solver_output(
            run_id="pms-synth",
            map_timeline=[{"mining_map": empty}, {"mining_map": empty}],
            map_after_pass1=empty,
            map_after_pass2=empty,
            map_after_routing=empty,
            map_final=empty,
            pass12_status_fields={},
            pass12_stats=pass12_stats,
            pass12_phase="test",
            pass12_skipped=True,
            pre_counts=_empty_counts(),
            post_pass2_counts=_empty_counts(),
            step4_result=step4,
            routing_state_summary=routing_state,
            post_step4_counts=_empty_counts(),
            unfinalized_placement_count=0,
            pass3_summary=pass3_summary,
            existing_layout_analysis=None,
            step_hash_step4=None,
            step_hash_pass3=None,
            step_hash_p4=None,
            solver_state_hash=None,
            replay_events=[],
            debug_location="tests.unit.shapez_asteroid.test_finalize_degradation_causes_success_tier",
        )

    pms = summary.get("preserve_missing_stub_summary") or {}
    assert int(pms.get("drop_count") or 0) == 2
    assert pms.get("by_reason", {}).get("NO_MATCHING_STUB") == 2
    pq = summary.get("preserve_quality") or {}
    assert int((pq.get("preserve_missing_stub_summary") or {}).get("drop_count") or 0) == 2


def test_success_tier_degradation_causes_include_internal_transport_baseline_warning() -> None:
    """optimization_warnings의 알려진 토큰이 termination.degradation_causes에 합류한다."""

    empty: list[dict[str, Any]] = []
    routing_state: dict[str, Any] = {"hard_protected_corridors": []}
    step4 = step4_routing_skipped_result(empty)
    good = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
        extractor_count=10,
        extension_count=0,
        transport_cell_count=0,
        transport_connectivity_ok=True,
    )
    pass12_stats: dict[str, Any] = {
        "pass12_merged_seed_miner_count": 10,
        "pass12_preserved_bundle_extractor_cells": 10,
        "pass12_preserved_missing_stub_drop_extractor_count": 0,
        "pass12_preserved_recovery_success_count": 0,
        "pass12_preserved_rotation_recovery_count": 0,
        "pass12_preserved_missing_stub_route_recovery_attempted_count": 0,
        "pass12_preserved_missing_stub_route_recovery_success_count": 0,
        "pass12_preserved_recovered_stub_samples": [],
        "pass12_preserved_unrecovered_stub_drop_samples": [],
        "pass2_probe_empty_goal_set_count": 0,
        "preserve_missing_stub_summary": {
            "drop_count": 0,
            "by_reason": {},
            "by_recoverability": {},
            "by_rejected_reason_subtype": {},
            "local_repack_candidate_count": 0,
        },
    }
    pass3_summary: dict[str, Any] = {
        "after_internal_transport_count": 50,
        "pass3_skipped": True,
        "pass3_committed": False,
    }
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize."
        "_validate_final_mining_layout",
        return_value=good,
    ):
        out, summary = build_final_solver_output(
            run_id="deg-causes-opt-warning",
            map_timeline=[{"mining_map": empty}, {"mining_map": empty}],
            map_after_pass1=empty,
            map_after_pass2=empty,
            map_after_routing=empty,
            map_final=empty,
            pass12_status_fields={},
            pass12_stats=pass12_stats,
            pass12_phase="test",
            pass12_skipped=True,
            pre_counts=_empty_counts(),
            post_pass2_counts=_empty_counts(),
            step4_result=step4,
            routing_state_summary=routing_state,
            post_step4_counts=_empty_counts(),
            unfinalized_placement_count=0,
            pass3_summary=pass3_summary,
            existing_layout_analysis=None,
            step_hash_step4=None,
            step_hash_pass3=None,
            step_hash_p4=None,
            solver_state_hash=None,
            replay_events=[],
            debug_location="tests.unit.shapez_asteroid.test_finalize_degradation_causes_success_tier",
            optimization_baseline_internal_transport=10,
        )

    assert OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE in summary.get(
        "optimization_warnings", []
    )
    dc = list((summary.get("termination") or {}).get("degradation_causes") or [])
    assert OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE in dc
    assert out["termination"] == summary["termination"]
