"""Regression: validation recovery loop iteration counts (off-by-one guard)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation import (
    constants as fc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import recovery_policy
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    solver_replay_events as solver_replay_ev,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    trace_run_scope,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (
    recovery_orchestrator as ro,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.p4_reclaim import (
    P4ReclaimStageResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.pass3 import (
    Pass3StageResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.pass12 import (
    Pass12StageResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.step4 import (
    Step4StageResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4RoutingResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation_contracts import (  # noqa: E501
    FinalValidationReport,
)


def _minimal_pass12() -> Pass12StageResult:
    return Pass12StageResult(
        map_after_pass1=[],
        map_after_pass2=[],
        pass12_stats={"placement_records": {}},
        pass12_skipped=False,
        pass12_mixed_surface_skipped=False,
        pass12_phase="post_pass2_mvp",
        pass12_status_fields={},
        pre_counts={},
        post_pass2_counts={},
        placement_records={},
        pass12_replay_txn_id=None,
    )


def _minimal_step4() -> Step4StageResult:
    s4r = Step4RoutingResult(
        committed=True,
        map_after_routing=[],
        routes=(),
        routing_failures=(),
        trunk_load={
            "unfinalized_placement_count": 0,
            "step4_route_count": 0,
            "step4_routing_failure_count": 0,
        },
        routing_state={"hard_protected_corridors": [], "soft_protected_corridors": []},
        placement_commit_by_id={},
        rolled_back_placement_ids=(),
        quarantined_placement_ids=(),
    )
    fv = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    return Step4StageResult(
        step4_result=s4r,
        map_after_routing=[],
        post_step4_counts={},
        routing_state_summary={},
        step_hash_step4="0" * 64,
        step4_replay_transaction_id=None,
        unfinalized_placement_count=0,
        report_step4=fv,
    )


def _minimal_p4() -> P4ReclaimStageResult:
    return P4ReclaimStageResult(
        map_final=[],
        pass3_summary={},
        step_hash_p4="0" * 64,
        solver_state_hash="0" * 64,
    )


def test_three_pass3_p4_finalize_cycles_when_validation_cap_is_two() -> None:
    """Cap 2 ⇒ two full Pass3→P4→finalize passes (``max_cycles``)."""

    calls = {"p3": 0, "p4": 0, "fin": 0}

    def _pass3(**_kwargs: object) -> Pass3StageResult:
        calls["p3"] += 1
        return Pass3StageResult(
            map_final=[],
            pass3_summary={},
            p3_trace={"protected_corridors": {"hard": [], "soft": []}},
            eligible_pass3=True,
            step_hash_pass3="0" * 64,
        )

    def _p4(**_kwargs: object) -> P4ReclaimStageResult:
        calls["p4"] += 1
        return _minimal_p4()

    fv_bad = {
        "geometry_valid": False,
        "connectivity_valid": True,
        "disconnected_stub_count": 0,
        "quarantined_unrouted_count": 0,
        "provisional_placed_row_count": 0,
        "orphan_transport_count": 0,
        "overlap_violation_count": 0,
        "missing_stub_count": 0,
        "missing_extractor_rotation_count": 0,
        "extractor_count": 0,
        "extension_count": 0,
        "transport_cell_count": 0,
        "transport_connectivity_ok": True,
    }

    def _finalize(**_kwargs: object) -> tuple[dict, dict]:
        calls["fin"] += 1
        out = {
            "ok": False,
            "return_reason": "validation_geometry_failed",
            "final_validation": fv_bad,
            "solver_timeline": [{"id": "stub", "summary": {}, "mining_map": []}],
            "solver_replay": {"events": [], "ui_frames": []},
            "solver_summary": {},
            "existing_layout_analysis": None,
        }
        summary = {
            "return_reason": "validation_geometry_failed",
            "pass3_commit_reason": None,
            "after_internal_transport_count": 0,
            "optimization_warnings": [],
            "recovery_context_chain": [],
        }
        return out, summary

    baseline_ns = SimpleNamespace(
        internal_transport_count=0,
        failure_reason=None,
        aggregation="sequential_trunk_v1",
    )

    with patch.object(ro, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
            with patch.object(ro, "validation_recovery_allowed", return_value=True):
                with patch(
                    "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                    "pass12.run_pass12_stage",
                    return_value=_minimal_pass12(),
                ):
                    with patch(
                        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                        "step4.run_step4_stage",
                        return_value=_minimal_step4(),
                    ):
                        with patch(
                            "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                            "pass3.run_pass3_stage",
                            side_effect=_pass3,
                        ):
                            with patch(
                                "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                                "p4_reclaim.run_p4_reclaim_stage",
                                side_effect=_p4,
                            ):
                                with patch(
                                    "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                                    "finalize.build_final_solver_output",
                                    side_effect=_finalize,
                                ):
                                    with patch(
                                        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver."
                                        "baseline_routing.compute_shortest_feasible_transport_baseline",
                                        return_value=baseline_ns,
                                    ):
                                        with patch(
                                            "django_apps.shapez_asteroid.services.blueprint_map_summary."
                                            "build_map_timeline",
                                            return_value=[{"mining_map": []}, {"mining_map": []}],
                                        ):
                                            with patch(
                                                "django_apps.shapez_asteroid.services.blueprint_map_summary."
                                                "merge_with_transport_and_final_mining_map",
                                                return_value=[],
                                            ):
                                                with patch(
                                                    "django_apps.shapez_asteroid.services."
                                                    "asteroid_mining_layout.existing_layout.existing_layout_analysis."
                                                    "analyze_existing_layout_from_mining_map",
                                                    return_value={},
                                                ):
                                                    with patch(
                                                        "django_apps.shapez_asteroid.services.asteroid_mining_layout."
                                                        "solver.solver_mutation_transaction.copy_mining_map_rows",
                                                        return_value=[],
                                                    ):
                                                        with trace_run_scope():
                                                            ro.run_solver_timeline_pipeline(
                                                                decoded={"BP": {"Entries": []}},
                                                                debug_location=(
                                                                    "tests.unit.shapez_asteroid."
                                                                    "test_recovery_orchestrator_loop"
                                                                ),
                                                                run_id="loop-count-guard",
                                                            )

    assert calls["p3"] == 2
    assert calls["p4"] == 2
    assert calls["fin"] == 2


def test_recovery_branch_includes_planned_actions_after_first_failure() -> None:
    """Second cycle RECOVERY_BRANCH payload lists ``planned_actions`` from prior STEP9 dict."""

    calls = {"fin": 0}
    fv_bad = {
        "geometry_valid": False,
        "connectivity_valid": True,
        "disconnected_stub_count": 0,
        "quarantined_unrouted_count": 0,
        "provisional_placed_row_count": 0,
        "orphan_transport_count": 0,
        "overlap_violation_count": 0,
        "missing_stub_count": 0,
        "missing_extractor_rotation_count": 0,
        "extractor_count": 0,
        "extension_count": 0,
        "transport_cell_count": 0,
        "transport_connectivity_ok": True,
    }
    fv_ok = {
        "geometry_valid": True,
        "connectivity_valid": True,
        "disconnected_stub_count": 0,
        "quarantined_unrouted_count": 0,
        "provisional_placed_row_count": 0,
        "orphan_transport_count": 0,
        "overlap_violation_count": 0,
        "missing_stub_count": 0,
        "missing_extractor_rotation_count": 0,
        "extractor_count": 0,
        "extension_count": 0,
        "transport_cell_count": 0,
        "transport_connectivity_ok": True,
    }

    def _finalize(**_kwargs: object) -> tuple[dict, dict]:
        calls["fin"] += 1
        n = calls["fin"]
        fv = fv_bad if n == 1 else fv_ok
        ok = n >= 2
        out = {
            "ok": ok,
            "return_reason": "ok" if ok else "validation_geometry_failed",
            "final_validation": fv,
            "solver_timeline": [{"id": "stub", "summary": {}, "mining_map": []}],
            "solver_replay": {"events": [], "ui_frames": []},
            "solver_summary": {},
            "existing_layout_analysis": None,
        }
        summary = {
            "return_reason": out["return_reason"],
            "pass3_commit_reason": "ok" if ok else None,
            "after_internal_transport_count": 0,
            "optimization_warnings": [],
            "recovery_context_chain": [],
        }
        return out, summary

    baseline_ns = SimpleNamespace(
        internal_transport_count=0,
        failure_reason=None,
        aggregation="sequential_trunk_v1",
    )

    replay_holder: dict[str, list] = {"events": []}

    def _capture_pass3(*, replay_events, **_k):
        replay_holder["events"] = replay_events
        return Pass3StageResult(
            map_final=[],
            pass3_summary={},
            p3_trace={"protected_corridors": {"hard": [], "soft": []}},
            eligible_pass3=True,
            step_hash_pass3="0" * 64,
        )

    with patch.object(ro, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
            with patch(
                "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                "pass12.run_pass12_stage",
                return_value=_minimal_pass12(),
            ):
                with patch(
                    "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                    "step4.run_step4_stage",
                    return_value=_minimal_step4(),
                ):
                    with patch(
                        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                        "pass3.run_pass3_stage",
                        side_effect=_capture_pass3,
                    ):
                        with patch(
                            "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                            "p4_reclaim.run_p4_reclaim_stage",
                            return_value=_minimal_p4(),
                        ):
                            with patch(
                                "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                                "finalize.build_final_solver_output",
                                side_effect=_finalize,
                            ):
                                with patch(
                                    "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver."
                                    "baseline_routing.compute_shortest_feasible_transport_baseline",
                                    return_value=baseline_ns,
                                ):
                                    with patch(
                                        "django_apps.shapez_asteroid.services.blueprint_map_summary."
                                        "build_map_timeline",
                                        return_value=[{"mining_map": []}, {"mining_map": []}],
                                    ):
                                        with patch(
                                            "django_apps.shapez_asteroid.services.blueprint_map_summary."
                                            "merge_with_transport_and_final_mining_map",
                                            return_value=[],
                                        ):
                                            with patch(
                                                "django_apps.shapez_asteroid.services."
                                                "asteroid_mining_layout.existing_layout.existing_layout_analysis."
                                                "analyze_existing_layout_from_mining_map",
                                                return_value={},
                                            ):
                                                with patch(
                                                    "django_apps.shapez_asteroid.services."
                                                    "asteroid_mining_layout.solver.solver_mutation_transaction."
                                                    "copy_mining_map_rows",
                                                    return_value=[],
                                                ):
                                                    with trace_run_scope():
                                                        ro.run_solver_timeline_pipeline(
                                                            decoded={"BP": {"Entries": []}},
                                                            debug_location=(
                                                                "tests.unit.shapez_asteroid."
                                                                "test_recovery_orchestrator_loop"
                                                            ),
                                                            run_id="planned-actions",
                                                        )

    branch_payloads = [
        e.get("payload")
        for e in replay_holder["events"]
        if e.get("kind") == solver_replay_ev.SolverMutationEventKind.RECOVERY_BRANCH.value
    ]
    assert len(branch_payloads) >= 1
    assert "planned_actions" in branch_payloads[0]
    assert fc.RECOVERY_ACTION_GEOMETRY_REPAIR_OR_FAIL in branch_payloads[0]["planned_actions"]
