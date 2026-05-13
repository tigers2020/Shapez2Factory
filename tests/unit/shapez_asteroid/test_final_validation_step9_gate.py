"""STEP9 final validation: hard invariants vs optimization / recovery contracts."""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import recovery_policy
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_policy import (
    step9_reports_hard_invariant_failure_for_bounded_recovery,
    validation_recovery_allowed,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    build_final_solver_output,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    step4_routing_skipped_result,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as _final_validation,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation_contracts import (  # noqa: E501
    FinalValidationReport,
)


def _empty_counts() -> dict[str, int]:
    return {"extractors": 0, "extensions": 0, "transport_cells": 0}


def test_orphan_pipe_only_fails_connectivity_while_belt_reaches_external() -> None:
    """Per-TransportKind subgraph: shape belt trunk ok, isolated fluid pipe is orphan."""

    mining_map: list[dict[str, Any]] = [
        {
            "x": 10,
            "y": 10,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "miner",
            "t": "Layout_ShapeMiner",
            "r": 0,
        },
        {"x": 11, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 12, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 13, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 14, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 15, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 16, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 17, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 18, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 19, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 20, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 10, "y": 12, "role": "pipe", "surface": "fluid"},
    ]
    r = _final_validation.validate_final_mining_layout(mining_map)
    assert r.orphan_shape_belt_count == 0
    assert r.orphan_fluid_pipe_count == 1
    assert r.orphan_transport_count == 1
    assert r.connectivity_valid is False


def test_fixed_output_stub_row_overwritten_fails_geometry() -> None:
    """Last row wins merge: fixed stub cell must remain belt/pipe (§15 geometry)."""

    mining_map: list[dict[str, Any]] = [
        {"x": 11, "y": 10, "role": "belt", "surface": "shape", "fixed_output_stub": True},
        {
            "x": 11,
            "y": 10,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "miner",
            "t": "Layout_ShapeMiner",
            "r": 2,
        },
    ]
    r = _final_validation.validate_final_mining_layout(mining_map)
    assert r.fixed_output_stub_removed_count == 1
    assert r.geometry_valid is False


def test_quarantined_unrouted_on_map_row_fails_geometry() -> None:
    mining_map = [
        {
            "x": 5,
            "y": 5,
            "role": "belt",
            "surface": "shape",
            "placement_state": "quarantined_unrouted",
        },
    ]
    r = _final_validation.validate_final_mining_layout(mining_map)
    assert r.quarantined_unrouted_count == 1
    assert r.geometry_valid is False


def test_quarantined_unrouted_cannot_pass_final_validation() -> None:
    """``placement_commit_state`` quarantined row must fail geometry (§15.1)."""

    mining_map = [
        {
            "x": 5,
            "y": 5,
            "role": "belt",
            "surface": "shape",
            "placement_commit_state": "quarantined_unrouted",
        },
    ]
    r = _final_validation.validate_final_mining_layout(mining_map)
    assert r.quarantined_unrouted_count == 1
    assert r.geometry_valid is False


def test_final_validation_rejects_orphan_transport_component_by_kind() -> None:
    """Orphan belt not reaching external margin → connectivity invalid + orphan count."""

    mining_map: list[dict[str, Any]] = [
        {
            "x": 10,
            "y": 10,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "miner",
            "t": "Layout_ShapeMiner",
            "r": 0,
        },
        {"x": 11, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 12, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 50, "y": 50, "role": "belt", "surface": "shape"},
    ]
    r = _final_validation.validate_final_mining_layout(mining_map)
    assert r.orphan_transport_count > 0
    assert r.orphan_shape_belt_count > 0
    assert r.connectivity_valid is False


def test_step9_bounded_recovery_not_eligible_when_fixed_stub_removed() -> None:
    fv: dict[str, Any] = {
        "geometry_valid": False,
        "connectivity_valid": True,
        "overlap_violation_count": 0,
        "quarantined_unrouted_count": 0,
        "missing_stub_count": 0,
        "fixed_output_stub_removed_count": 1,
    }
    assert step9_reports_hard_invariant_failure_for_bounded_recovery(fv) is False
    out = {"ok": False, "return_reason": "validation_geometry_failed", "final_validation": fv}
    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        assert validation_recovery_allowed(out) is False


def test_step9_bounded_recovery_ignores_summary_only_optimization_signals() -> None:
    """Hard-invariant predicate reads ``final_validation`` only (no optimization keys)."""

    fv: dict[str, Any] = {
        "geometry_valid": True,
        "connectivity_valid": True,
        "overlap_violation_count": 0,
        "quarantined_unrouted_count": 0,
        "missing_stub_count": 0,
        "fixed_output_stub_removed_count": 0,
        "optimization_warnings": ["internal_transport_above_pass2_baseline"],
        "internal_transport_delta_vs_baseline": 99,
    }
    assert step9_reports_hard_invariant_failure_for_bounded_recovery(fv) is False


def test_finalize_optimization_warning_keeps_success_when_layout_hard_valid() -> None:
    """Baseline vs final internal transport warning is quality tier, not STEP9 hard fail."""

    empty: list[dict[str, Any]] = []
    step4 = step4_routing_skipped_result(empty)
    tl = dict(step4.trunk_load)
    tl.setdefault("step4_routing_failure_count", 0)
    step4_ok = replace(
        step4,
        committed=True,
        complete_routing_success=True,
        rolled_back_placement_ids=tuple(),
        quarantined_placement_ids=tuple(),
        trunk_load=tl,
    )

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
        extractor_count=0,
        extension_count=0,
        transport_cell_count=0,
        transport_connectivity_ok=True,
    )

    pass3_summary: dict[str, Any] = {
        "after_internal_transport_count": 50,
        "pass3_skipped": False,
        "pass3_committed": True,
        "pass3_final_committed": True,
    }

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize."
        "_validate_final_mining_layout",
        return_value=good,
    ):
        out, summary = build_final_solver_output(
            run_id="step9-opt-warn",
            map_timeline=[{"mining_map": empty}, {"mining_map": empty}],
            map_after_pass1=empty,
            map_after_pass2=empty,
            map_after_routing=empty,
            map_final=empty,
            pass12_status_fields={},
            pass12_stats={},
            pass12_phase="test",
            pass12_skipped=False,
            pre_counts=_empty_counts(),
            post_pass2_counts=_empty_counts(),
            step4_result=step4_ok,
            routing_state_summary=None,
            post_step4_counts=_empty_counts(),
            unfinalized_placement_count=0,
            pass3_summary=pass3_summary,
            existing_layout_analysis=None,
            step_hash_step4=None,
            step_hash_pass3=None,
            step_hash_p4=None,
            solver_state_hash=None,
            replay_events=[],
            debug_location="tests.unit.shapez_asteroid.test_final_validation_step9_gate",
            optimization_baseline_internal_transport=10,
            optimization_baseline_internal_transport_post_step4=10,
            optimization_counterfactual_internal_transport_sequential_v1=100,
            optimization_counterfactual_failure_reason="",
            optimization_counterfactual_aggregation="",
        )

    assert out["ok"] is True
    assert summary["solver_termination"] == "success"
    assert summary["optimization_warnings"]
    fv = out.get("final_validation") or {}
    assert fv.get("geometry_valid") is True
    assert fv.get("connectivity_valid") is True
    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        assert validation_recovery_allowed(out) is False
