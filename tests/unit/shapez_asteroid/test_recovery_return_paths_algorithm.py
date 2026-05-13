"""§4.3 recovery return paths: invariants vs Algorithm (regression, not snapshots).

Policy rows mirror Algorithm ``02_pipeline_control_flow`` §4.3 / §4.3.1 / §4.3.2 and
``13_step9_validation`` §15 (see ``recovery_return_policy.py``).
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    RECOVERY_TRIGGER_FINAL_VALIDATION_FAILURE,
    RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK,
    RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK,
    RECOVERY_TRIGGER_RECLAIM_INCREMENTAL_FAILURE,
    RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE,
    RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    recovery_policy,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    recovery_return_policy as rrp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_policy import (
    validation_recovery_allowed,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (
    p4_reclaim as p4_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (
    recovery_orchestrator as ro,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.p4_reclaim import (
    P4ReclaimStageResult,
)


def _clean_fv() -> dict[str, Any]:
    return {
        "geometry_valid": True,
        "connectivity_valid": True,
        "overlap_violation_count": 0,
        "quarantined_unrouted_count": 0,
        "missing_stub_count": 0,
    }


def _mining_layout_service_root() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "django_apps"
        / "shapez_asteroid"
        / "services"
        / "asteroid_mining_layout"
    )


def test_solver_pipeline_does_not_iterate_replay_events_for_policy() -> None:
    """Replay is append-only export; no ``for`` / comprehension scans ``replay_events`` (§14)."""

    root = _mining_layout_service_root() / "solver_pipeline"
    bad: list[str] = []
    for path in sorted(root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and isinstance(node.iter, ast.Name):
                if node.iter.id == "replay_events":
                    bad.append(f"{path.name}:For")
            if isinstance(node, ast.comprehension) and isinstance(node.iter, ast.Name):
                if node.iter.id == "replay_events":
                    bad.append(f"{path.name}:comp")
    assert not bad, bad


def test_d2_b2_orchestrator_step4_routing_contract_in_source() -> None:
    """D2-B2-DEL: policy hook, one remedial STEP4, no STEP4 inside validation loop, routing gate."""

    src = inspect.getsource(ro.run_solver_timeline_pipeline)
    assert "_recovery_return_policy.recovery_return_policy_for_trigger" in src
    assert "RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE" in src
    assert "run_step4_stage(" in src
    marker = "for va in range(max_cycles):"
    assert marker in src
    tail = src[src.index(marker) :]
    assert "run_step4_stage(" not in tail
    assert "step4_recovery_trigger" in src
    assert "recovery_pass3_connectivity_break" in src
    assert "copy_mining_map_rows(step4.map_after_routing)" in src


def test_validation_recovery_not_enabled_by_post_reclaim_flag_when_step9_clean() -> None:
    """§4.3.2: post-reclaim connectivity tag is not a substitute for STEP9 hard invariant."""

    out: dict[str, Any] = {
        "ok": False,
        "return_reason": "partial_success",
        "final_validation": _clean_fv(),
        "recovery_post_reclaim_pass3_connectivity_break": True,
    }
    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        assert validation_recovery_allowed(out) is False


def test_validation_recovery_allowed_ignores_cascade_corrective_attempts() -> None:
    """STEP4 cascade counter must not gate validation recovery (separate contracts)."""

    out: dict[str, Any] = {
        "ok": False,
        "return_reason": "validation_connectivity_failed",
        "final_validation": {**_clean_fv(), "connectivity_valid": False},
        "cascade_corrective_attempts": 999,
    }
    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        assert validation_recovery_allowed(out) is True


def test_p4_reclaim_stage_invokes_post_reclaim_pass3_hook_at_most_once() -> None:
    """§4.3.2: single post-reclaim Pass3 rerun block per P4 stage (no inner rerun loop)."""

    src = inspect.getsource(p4_mod.run_p4_reclaim_stage)
    assert src.count("_run_post_reclaim_pass3_once(") == 1
    assert "post_reclaim_pass3_reruns_lifetime" in src


def test_p4_reclaim_stage_accepts_solve_global_recovery_budgets_param() -> None:
    sig = inspect.signature(p4_mod.run_p4_reclaim_stage)
    assert "solver_recovery_budgets" in sig.parameters


def test_orchestrator_forwards_solver_recovery_budgets_to_p4() -> None:
    src = inspect.getsource(ro.run_solver_timeline_pipeline)
    assert "solver_recovery_budgets=solver_recovery_budgets" in src


def test_tag_pass3_connectivity_break_sets_recovery_trigger_first_cycle_only() -> None:
    """§4.3.1: greedy connectivity-only trace tags summary; validation cycles do not re-tag."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
        PASS3_GREEDY_REJECT_DETAIL_CONNECTIVITY,
        RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_policy import (
        apply_recovery_contract_defaults,
        tag_pass3_connectivity_break_from_greedy_trace,
    )

    s: dict[str, Any] = {}
    apply_recovery_contract_defaults(s)
    tr = {
        "pass3_connectivity_reject_sample": {"a": 1},
        "pass3_greedy_reject_detail": PASS3_GREEDY_REJECT_DETAIL_CONNECTIVITY,
    }
    tag_pass3_connectivity_break_from_greedy_trace(s, tr, validation_recovery_attempt=0)
    assert s.get("recovery_pass3_connectivity_break") is True
    assert s.get("recovery_trigger") == RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK
    tag_pass3_connectivity_break_from_greedy_trace(s, tr, validation_recovery_attempt=1)
    assert s.get("recovery_trigger") == RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK


def test_recovery_return_policy_triggers_exactly_six() -> None:
    assert rrp.recovery_return_policy_triggers() == frozenset(
        {
            RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
            RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE,
            RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK,
            RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK,
            RECOVERY_TRIGGER_RECLAIM_INCREMENTAL_FAILURE,
            RECOVERY_TRIGGER_FINAL_VALIDATION_FAILURE,
        }
    )


def test_pass3_connectivity_break_has_return_policy_row() -> None:
    """§4.3.1: greedy Pass3 connectivity-only rollback maps to explicit return policy."""

    p = rrp.recovery_return_policy_for_trigger(RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK)
    assert p.reenters_step4 is False
    assert p.primary_return_steps == ("STEP6",)


def test_recovery_return_policy_table_matches_algorithm() -> None:
    """§4.3: module table is the single source; public API returns identical rows."""

    for trigger, row in rrp._POLICY_TABLE.items():
        assert rrp.recovery_return_policy_for_trigger(trigger) is row


def test_final_validation_failure_policy_never_targets_step4() -> None:
    """§4.3 / §15: final validation recovery has no STEP4 return leg."""

    p = rrp.recovery_return_policy_for_trigger(RECOVERY_TRIGGER_FINAL_VALIDATION_FAILURE)
    assert p.reenters_step4 is False
    assert "STEP4" not in p.primary_return_steps
    assert p.primary_return_steps == ("Pass3", "P4", "STEP9")


def test_post_reclaim_pass3_connectivity_break_policy_disallows_extra_rerun() -> None:
    """§4.3.2: no second post-reclaim Pass3 rerun inside the same reclaim block."""

    p = rrp.recovery_return_policy_for_trigger(
        RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK,
    )
    assert p.allows_extra_post_reclaim_pass3_rerun is False
    assert p.primary_return_steps == ("STEP9",)


def test_each_section_4_3_trigger_has_distinct_return_policy_row() -> None:
    """§4.3: six canonical triggers each resolve to one frozen policy row."""

    for trigger in sorted(rrp.recovery_return_policy_triggers()):
        row = rrp.recovery_return_policy_for_trigger(trigger)
        assert row.policy_id
        assert isinstance(row.primary_return_steps, tuple)
        assert row.primary_return_steps


def test_reclaim_incremental_failure_tag_matches_section_4_3_row() -> None:
    """§4.3 ``reclaim_incremental_failure``: P4 rollback flag → policy row (no STEP4 re-entry)."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_policy import (
        apply_recovery_contract_defaults,
        tag_reclaim_incremental_failure_from_summary,
    )

    s: dict[str, Any] = {}
    apply_recovery_contract_defaults(s)
    s["p4_reclaim_incremental_route_rollback_performed"] = True
    tag_reclaim_incremental_failure_from_summary(s)
    assert s.get("recovery_reclaim_incremental_failure") is True
    pol = rrp.recovery_return_policy_for_trigger(RECOVERY_TRIGGER_RECLAIM_INCREMENTAL_FAILURE)
    assert pol.reenters_step4 is False
    assert pol.primary_return_steps == ("STEP6",)


def test_append_recovery_return_policy_trace_entries_pass3_and_step4() -> None:
    """Trace helper mirrors ``recovery_return_policy_for_trigger`` for active summary flags."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
        RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_policy import (
        append_recovery_return_policy_trace_entries,
        apply_recovery_contract_defaults,
    )

    s: dict[str, Any] = {
        "recovery_pass3_connectivity_break": True,
        "step4_recovery_trigger": RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
    }
    apply_recovery_contract_defaults(s)
    append_recovery_return_policy_trace_entries(s)
    tr = s.get("recovery_return_policy_trace")
    assert isinstance(tr, list) and len(tr) == 2
    ids = {e["recovery_trigger"] for e in tr}
    assert RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK in ids
    assert RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE in ids


def test_post_reclaim_tag_preserves_incremental_on_recovery_trigger_parallel() -> None:
    """Dual failure: primary ``recovery_trigger`` stays post-reclaim; incremental is parallel."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_policy import (
        apply_recovery_contract_defaults,
        tag_post_reclaim_pass3_connectivity_break,
    )

    s: dict[str, Any] = {
        "post_reclaim_pass3_pass3_reverted": True,
        "recovery_reclaim_incremental_failure": True,
    }
    apply_recovery_contract_defaults(s)
    tag_post_reclaim_pass3_connectivity_break(s)
    assert s["recovery_trigger"] == RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK
    assert s.get("recovery_trigger_parallel") == [RECOVERY_TRIGGER_RECLAIM_INCREMENTAL_FAILURE]


def test_run_step4_stage_invoked_once_without_routing_remedial() -> None:
    """validation_recovery loop runs Pass3→P4 again; ``run_step4_stage`` is not re-entered."""

    from unittest.mock import patch

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import recovery_policy
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
        trace_run_scope,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.pass3 import (
        Pass3StageResult,
    )
    from tests.unit.shapez_asteroid.test_recovery_orchestrator_loop import (
        _minimal_p4,
        _minimal_pass12,
        _minimal_step4,
    )

    calls = {"p3": 0, "p4": 0, "fin": 0, "s4": 0}

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

    def _finalize(**_kwargs: object) -> tuple[dict[str, Any], dict[str, Any]]:
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

    def _counting_step4(*_a: object, **_k: object) -> object:
        calls["s4"] += 1
        return _minimal_step4()

    from types import SimpleNamespace

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
                        side_effect=_counting_step4,
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
                                                                    "test_recovery_return_paths_algorithm"
                                                                ),
                                                                run_id="s4-call-count",
                                                            )

    assert calls["s4"] == 1
    assert calls["p3"] == 2


def test_run_step4_stage_twice_when_step4_routing_failure_remedial_runs() -> None:
    """§4.3 step4_routing_failure: at most one remedial ``run_step4_stage`` before Pass3 loop."""

    from unittest.mock import patch

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import recovery_policy
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
        trace_run_scope,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.pass3 import (
        Pass3StageResult,
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
    from tests.unit.shapez_asteroid.test_recovery_orchestrator_loop import (
        _minimal_p4,
        _minimal_pass12,
        _minimal_step4,
    )

    def _step4_fail() -> Step4StageResult:
        s4r = Step4RoutingResult(
            committed=False,
            map_after_routing=[],
            routes=(),
            routing_failures=(),
            trunk_load={"unfinalized_placement_count": 0},
            routing_state={"hard_protected_corridors": [], "soft_protected_corridors": []},
            placement_commit_by_id={},
            rolled_back_placement_ids=(),
            quarantined_placement_ids=(),
            complete_routing_success=False,
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

    calls = {"s4": 0}

    def _step4_sequence(*_a: object, **_k: object) -> Step4StageResult:
        calls["s4"] += 1
        if calls["s4"] == 1:
            return _step4_fail()
        return _minimal_step4()

    def _pass3(**_kwargs: object) -> Pass3StageResult:
        return Pass3StageResult(
            map_final=[],
            pass3_summary={},
            p3_trace={"protected_corridors": {"hard": [], "soft": []}},
            eligible_pass3=True,
            step_hash_pass3="0" * 64,
        )

    def _finalize(**_kwargs: object) -> tuple[dict[str, Any], dict[str, Any]]:
        out = {
            "ok": True,
            "return_reason": "ok",
            "final_validation": {
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
            },
            "solver_timeline": [{"id": "stub", "summary": {}, "mining_map": []}],
            "solver_replay": {"events": [], "ui_frames": []},
            "solver_summary": {},
            "existing_layout_analysis": None,
        }
        summary = {
            "return_reason": "ok",
            "pass3_commit_reason": None,
            "after_internal_transport_count": 0,
            "optimization_warnings": [],
            "recovery_context_chain": [],
        }
        return out, summary

    from types import SimpleNamespace

    baseline_ns = SimpleNamespace(
        internal_transport_count=0,
        failure_reason=None,
        aggregation="sequential_trunk_v1",
    )

    with patch.object(ro, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 1):
        with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 1):
            with patch(
                "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                "pass12.run_pass12_stage",
                return_value=_minimal_pass12(),
            ):
                with patch(
                    "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                    "step4.run_step4_stage",
                    side_effect=_step4_sequence,
                ):
                    with patch(
                        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                        "pass3.run_pass3_stage",
                        side_effect=_pass3,
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
                                                    "django_apps.shapez_asteroid.services.asteroid_mining_layout."
                                                    "solver.solver_mutation_transaction.copy_mining_map_rows",
                                                    return_value=[],
                                                ):
                                                    with trace_run_scope():
                                                        ro.run_solver_timeline_pipeline(
                                                            decoded={"BP": {"Entries": []}},
                                                            debug_location=(
                                                                "tests.unit.shapez_asteroid."
                                                                "test_recovery_return_paths_algorithm"
                                                            ),
                                                            run_id="s4-remedial-count",
                                                        )

    assert calls["s4"] == 2


def test_recovery_return_policy_unknown_trigger_raises() -> None:
    with pytest.raises(ValueError, match="unknown recovery trigger"):
        rrp.recovery_return_policy_for_trigger("not_in_section_4_3_table")
