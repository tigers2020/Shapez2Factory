"""PR4-D: Algorithm §14 / §15 assertion boundary — invariant tests.

Not implementation snapshots: asserts contract against Algorithm intent.
"""

from __future__ import annotations

import copy
import inspect
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
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import final_validation
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation_contracts import (  # noqa: E501
    FinalValidationReport,
)


def _empty_counts() -> dict[str, int]:
    return {"extractors": 0, "extensions": 0, "transport_cells": 0}


def _fv(**kwargs: object) -> dict[str, object]:
    base: dict[str, object] = {
        "geometry_valid": True,
        "connectivity_valid": True,
        "overlap_violation_count": 0,
        "quarantined_unrouted_count": 0,
        "missing_stub_count": 0,
    }
    base.update(kwargs)
    return base


def test_validate_final_mining_layout_is_map_only_assertion_api() -> None:
    """§15: STEP9 entrypoint is an assertion gate on ``mining_map`` rows only (no routing_state)."""

    sig = inspect.signature(final_validation.validate_final_mining_layout)
    assert list(sig.parameters) == ["mining_map"]


def test_step9_hard_invariant_predicate_matches_recovery_contract() -> None:
    """Helper must stay aligned with ``validation_recovery_allowed`` STEP9 branch."""

    fv_connectivity = _fv(connectivity_valid=False)
    out_c = {
        "ok": False,
        "return_reason": "validation_connectivity_failed",
        "final_validation": fv_connectivity,
    }
    assert step9_reports_hard_invariant_failure_for_bounded_recovery(fv_connectivity) is True
    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        assert validation_recovery_allowed(out_c) is True

    fv_clean = _fv()
    out_partial = {
        "ok": False,
        "return_reason": "step4_partial_failure",
        "final_validation": fv_clean,
    }
    assert step9_reports_hard_invariant_failure_for_bounded_recovery(fv_clean) is False
    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        assert validation_recovery_allowed(out_partial) is False


def test_validation_recovery_not_triggered_partial_success_clean_step9() -> None:
    """§15: ``ok`` False alone must not enable retry without a STEP9 hard invariant fail."""

    out = {
        "ok": False,
        "return_reason": "step4_partial_failure",
        "final_validation": _fv(),
    }
    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        assert validation_recovery_allowed(out) is False


def test_finalize_preserves_routing_state_and_does_not_promote_ela_to_hard() -> None:
    """§14: finalize echoes ``routing_state`` by reference; ELA seeds stay out of ``hard``."""

    empty: list[dict[str, Any]] = []
    routing_state: dict[str, Any] = {
        "hard_protected_corridors": [[2, 3]],
        "soft_protected_corridors": [[4, 5]],
        "ela_trunk_seed_candidate_corridors": [[9, 9]],
    }
    snapshot = copy.deepcopy(routing_state)
    step4 = step4_routing_skipped_result(empty)
    step4_with_rs = replace(step4, routing_state=routing_state)

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
            run_id="pr4d-routing-state",
            map_timeline=[{"mining_map": empty}, {"mining_map": empty}],
            map_after_pass1=empty,
            map_after_pass2=empty,
            map_after_routing=empty,
            map_final=empty,
            pass12_status_fields={},
            pass12_stats={},
            pass12_phase="test",
            pass12_skipped=True,
            pre_counts=_empty_counts(),
            post_pass2_counts=_empty_counts(),
            step4_result=step4_with_rs,
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
            debug_location="tests.unit.shapez_asteroid.test_pr4d_algorithm_final_validation_boundary",
        )

    assert summary["routing_state"] is routing_state
    assert routing_state == snapshot
    ela = routing_state.get("ela_trunk_seed_candidate_corridors")
    hard = routing_state.get("hard_protected_corridors")
    assert isinstance(ela, list) and isinstance(hard, list)
    assert [9, 9] not in hard


def test_recovery_timeline_loop_does_not_call_step4_twice() -> None:
    """§11/§15: validation recovery does not re-enter STEP4 (single ``run_step4_stage`` call)."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (
        recovery_orchestrator as ro,
    )

    src = inspect.getsource(ro.run_solver_timeline_pipeline)
    assert src.count("run_step4_stage(") == 1
