"""Optimization baseline: Pass1·Pass2 pre-STEP4 snapshot vs final internal transport.

``optimization_baseline_internal_transport``는 BFS shortest가 아니다. Pass3와 동일한 단일
transport_kind 기준 **pre-STEP4 내부 transport 타일 수**
(``optimization_baseline_internal_transport_pre_step4``).
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.existing_layout_analysis import (  # noqa: E501
    analyze_existing_layout_from_mining_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation import constants as fc
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
    optimization_baseline_internal_transport_pre_step4,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    SOLVER_TERMINATION_FAILURE,
    SOLVER_TERMINATION_PARTIAL_SUCCESS,
    SOLVER_TERMINATION_SUCCESS,
    _append_optimization_warnings,
    _append_stub_route_recovery_disabled_warning,
    _compute_solver_quality_tier,
    _solver_quality_summary_for_tier,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.pass12 import (
    run_pass12_stage,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.step4 import (
    run_step4_stage,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as final_val,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline


def _decoded_miners_with_belt_escape() -> dict:
    entries: list[dict] = []
    for x in range(10, 13):
        entries.append({"X": x, "Y": 0, "T": "Layout_ShapeMiner"})
    for x in range(13, 30):
        entries.append({"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0})
    return {"BP": {"Entries": entries}}


def _expected_pre_post_step4_baselines(decoded: dict) -> tuple[int | None, int | None]:
    """Same Pass12→STEP4 snapshot inputs as ``run_solver_timeline_pipeline`` (pre Pass3)."""

    map_timeline = build_map_timeline(decoded)
    working_map = map_timeline[0]["mining_map"]
    final_map = map_timeline[-1]["mining_map"]
    is_external = final_val.external_predicate_for_mining_map(map_timeline[1]["mining_map"])
    existing_layout_analysis = analyze_existing_layout_from_mining_map(
        working_map,
        is_external=is_external,
    )
    replay_events: list = []
    pass12 = run_pass12_stage(
        working_map=working_map,
        final_map=final_map,
        is_external=is_external,
        existing_layout_analysis=existing_layout_analysis,
        replay_events=replay_events,
        map_timeline=map_timeline,
        debug_location="tests.unit.shapez_asteroid.test_optimization_baseline",
    )
    pre = optimization_baseline_internal_transport_pre_step4(
        pass12.map_after_pass2,
        final_mining_map=final_map,
        is_external=is_external,
    )
    step4 = run_step4_stage(
        map_after_pass2=pass12.map_after_pass2,
        final_map=final_map,
        is_external=is_external,
        placement_records=pass12.placement_records,
        pass12_skipped=pass12.pass12_skipped,
        pass12_replay_txn_id=pass12.pass12_replay_txn_id,
        replay_events=replay_events,
        debug_location="tests.unit.shapez_asteroid.test_optimization_baseline",
    )
    post = optimization_baseline_internal_transport_pre_step4(
        step4.map_after_routing,
        final_mining_map=final_map,
        is_external=is_external,
    )
    return pre, post


def test_optimization_baseline_uses_pre_step4_snapshot() -> None:
    decoded = _decoded_miners_with_belt_escape()
    expected_pre, expected_post = _expected_pre_post_step4_baselines(decoded)
    out = build_solver_timeline(decoded)
    summ = out["solver_summary"]
    assert summ["optimization_baseline_internal_transport"] == expected_pre
    assert summ["optimization_baseline_internal_transport_post_step4"] == expected_post
    fv = out["final_validation"]
    assert fv["optimization_baseline_internal_transport"] == expected_pre
    assert fv["optimization_baseline_internal_transport_post_step4"] == expected_post
    assert fv["optimization_baseline_snapshot_kind"] == (
        fc.OPTIMIZATION_BASELINE_SNAPSHOT_PASS1_PASS2_PRE_STEP4
    )
    assert fv["optimization_final_internal_transport_count"] == summ.get(
        "after_internal_transport_count"
    )


def test_optimization_warning_when_final_internal_transport_above_baseline() -> None:
    out = build_solver_timeline(_decoded_miners_with_belt_escape())
    summ = out["solver_summary"]
    base = summ.get("optimization_baseline_internal_transport")
    fin = summ.get("after_internal_transport_count")
    warns = list(summ.get("optimization_warnings") or [])
    fv_warns = list(out["final_validation"].get("optimization_warnings") or [])
    replay_warns = list(
        (out["solver_replay"].get("optimization_metrics") or {}).get("optimization_warnings") or []
    )
    assert warns == fv_warns == replay_warns
    if isinstance(base, int) and isinstance(fin, int) and fin > base:
        assert fc.OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE in warns
        drop_n = int(summ.get("extractor_drop_count") or 0)
        if drop_n > 0:
            assert (
                summ.get("solver_quality_tier")
                == fc.SOLVER_QUALITY_TIER_PARTIAL_SUCCESS_VALID_PRESERVE_LOSS
            )
            assert summ.get("solver_quality_summary") == _solver_quality_summary_for_tier(
                fc.SOLVER_QUALITY_TIER_PARTIAL_SUCCESS_VALID_PRESERVE_LOSS
            )
        else:
            assert (
                summ.get("solver_quality_tier")
                == fc.SOLVER_QUALITY_TIER_SUCCESS_VALID_WITH_OPTIMIZATION_WARNING
            )
            assert summ.get("solver_quality_summary") == _solver_quality_summary_for_tier(
                fc.SOLVER_QUALITY_TIER_SUCCESS_VALID_WITH_OPTIMIZATION_WARNING
            )
        assert summ.get("solver_result_tier") == summ.get("solver_quality_tier")
        assert int(summ.get("optimization_warning_count") or 0) >= 1
        assert isinstance(summ.get("internal_transport_delta_vs_baseline"), int)
        assert out["termination"].get("quality_tier") == summ.get("solver_quality_tier")
    else:
        assert base is None or fin is None or fin <= base
        assert fc.OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE not in warns


def test_compute_solver_quality_tier_extractor_drop_beats_optimization_warning() -> None:
    """Preserve/extractor loss is reported as partial tier even if optimization warnings exist."""

    assert (
        _compute_solver_quality_tier(
            layout_hard_valid=True,
            solver_termination=SOLVER_TERMINATION_SUCCESS,
            optimization_warnings=[fc.OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE],
            extractor_drop_count=1,
            preserve_source_loss_before_step4=0,
        )
        == fc.SOLVER_QUALITY_TIER_PARTIAL_SUCCESS_VALID_PRESERVE_LOSS
    )


def test_compute_solver_quality_tier_optimization_warning_branch() -> None:
    assert (
        _compute_solver_quality_tier(
            layout_hard_valid=True,
            solver_termination=SOLVER_TERMINATION_SUCCESS,
            optimization_warnings=[fc.OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE],
            extractor_drop_count=0,
            preserve_source_loss_before_step4=0,
        )
        == fc.SOLVER_QUALITY_TIER_SUCCESS_VALID_WITH_OPTIMIZATION_WARNING
    )


def test_compute_solver_quality_tier_extractor_drop_partial() -> None:
    assert (
        _compute_solver_quality_tier(
            layout_hard_valid=True,
            solver_termination=SOLVER_TERMINATION_SUCCESS,
            optimization_warnings=[],
            extractor_drop_count=1,
            preserve_source_loss_before_step4=0,
        )
        == fc.SOLVER_QUALITY_TIER_PARTIAL_SUCCESS_VALID_PRESERVE_LOSS
    )


def test_compute_solver_quality_tier_preserve_source_loss_before_step4() -> None:
    assert (
        _compute_solver_quality_tier(
            layout_hard_valid=True,
            solver_termination=SOLVER_TERMINATION_SUCCESS,
            optimization_warnings=[],
            extractor_drop_count=0,
            preserve_source_loss_before_step4=2,
        )
        == fc.SOLVER_QUALITY_TIER_PARTIAL_SUCCESS_VALID_PRESERVE_LOSS
    )


def test_compute_solver_quality_tier_hard_layout_invalid() -> None:
    assert (
        _compute_solver_quality_tier(
            layout_hard_valid=False,
            solver_termination=SOLVER_TERMINATION_SUCCESS,
            optimization_warnings=[],
            extractor_drop_count=0,
            preserve_source_loss_before_step4=0,
        )
        == fc.SOLVER_QUALITY_TIER_SOLVER_FAILURE
    )


def test_compute_solver_quality_tier_partial_success_maps_partial_tier() -> None:
    assert (
        _compute_solver_quality_tier(
            layout_hard_valid=True,
            solver_termination=SOLVER_TERMINATION_PARTIAL_SUCCESS,
            optimization_warnings=[],
            extractor_drop_count=0,
            preserve_source_loss_before_step4=0,
        )
        == fc.SOLVER_QUALITY_TIER_PARTIAL_SUCCESS_VALID_PRESERVE_LOSS
    )


def test_compute_solver_quality_tier_solver_failure() -> None:
    assert (
        _compute_solver_quality_tier(
            layout_hard_valid=True,
            solver_termination=SOLVER_TERMINATION_FAILURE,
            optimization_warnings=[],
            extractor_drop_count=0,
            preserve_source_loss_before_step4=0,
        )
        == fc.SOLVER_QUALITY_TIER_SOLVER_FAILURE
    )


def test_optimization_baseline_is_reported_in_solver_replay_metrics() -> None:
    out = build_solver_timeline(_decoded_miners_with_belt_escape())
    om = out["solver_replay"]["optimization_metrics"]
    summ = out["solver_summary"]
    assert om["baseline_snapshot_kind"] == fc.OPTIMIZATION_BASELINE_SNAPSHOT_PASS1_PASS2_PRE_STEP4
    assert (
        om["baseline_internal_transport_count"] == summ["optimization_baseline_internal_transport"]
    )
    assert (
        om["baseline_internal_transport_post_step4_count"]
        == summ["optimization_baseline_internal_transport_post_step4"]
    )
    assert om["final_internal_transport_count"] == summ.get("after_internal_transport_count")
    assert om["optimization_warnings"] == list(summ.get("optimization_warnings") or [])
    assert om["counterfactual_internal_transport_sequential_v1"] == summ.get(
        "optimization_counterfactual_internal_transport_sequential_v1"
    )
    assert om["counterfactual_aggregation"] == summ.get("optimization_counterfactual_aggregation")
    assert om["counterfactual_failure_reason"] == summ.get(
        "optimization_counterfactual_failure_reason"
    )
    assert om["internal_transport_quality_ratio"] == summ.get(
        "optimization_internal_transport_quality_ratio"
    )


def test_optimization_warning_when_quality_ratio_above_counterfactual_threshold() -> None:
    summary = {
        "optimization_baseline_internal_transport": 100,
        "after_internal_transport_count": 90,
        "optimization_internal_transport_quality_ratio": 1.4,
    }
    _append_optimization_warnings(summary)
    warns = list(summary.get("optimization_warnings") or [])
    assert fc.OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_QUALITY_RATIO_HIGH in warns
    assert fc.OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE not in warns


def test_compute_solver_quality_tier_fully_optimized() -> None:
    assert (
        _compute_solver_quality_tier(
            layout_hard_valid=True,
            solver_termination=SOLVER_TERMINATION_SUCCESS,
            optimization_warnings=[],
            extractor_drop_count=0,
            preserve_source_loss_before_step4=0,
        )
        == fc.SOLVER_QUALITY_TIER_SUCCESS_VALID_OPTIMIZED
    )


def test_optimization_no_quality_ratio_warning_at_threshold() -> None:
    summary = {
        "optimization_baseline_internal_transport": 100,
        "after_internal_transport_count": 90,
        "optimization_internal_transport_quality_ratio": 1.35,
    }
    _append_optimization_warnings(summary)
    warns = list(summary.get("optimization_warnings") or [])
    assert fc.OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_QUALITY_RATIO_HIGH not in warns


def test_stub_route_recovery_disabled_while_eligible_warning() -> None:
    summary = {
        "optimization_warnings": [],
        "optimization_warning_count": 0,
        "pass12_stub_route_recovery_enabled": False,
        "pass12_stub_route_recovery_eligible_count": 3,
    }
    _append_stub_route_recovery_disabled_warning(summary)
    assert (
        fc.OPTIMIZATION_WARNING_PASS12_STUB_ROUTE_RECOVERY_DISABLED_WHILE_ELIGIBLE
        in summary["optimization_warnings"]
    )
    assert summary["optimization_warning_count"] == 1


def test_stub_route_recovery_disabled_while_eligible_no_op_when_enabled() -> None:
    summary = {
        "optimization_warnings": [],
        "optimization_warning_count": 0,
        "pass12_stub_route_recovery_enabled": True,
        "pass12_stub_route_recovery_eligible_count": 3,
    }
    _append_stub_route_recovery_disabled_warning(summary)
    assert summary["optimization_warnings"] == []
