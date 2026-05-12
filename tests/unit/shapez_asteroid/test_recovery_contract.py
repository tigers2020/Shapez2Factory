"""P5 recovery contract: validation router, outcome rollup, optimization warnings."""

from __future__ import annotations

import copy
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation import constants as fc
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
    protected_corridors_for_reclaim,
    protected_corridors_read_for_reclaim,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTRACTORS_FLUID,
    EXTRACTORS_SHAPE,
    layout_kind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import recovery_policy
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    solver_replay_events as solver_replay_ev,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_context import (
    finalize_recovery_terminal_reason,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_policy import (
    synthesize_recovery_validation_outcome,
    validation_recovery_allowed,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    trace_run_scope,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (
    recovery_orchestrator as recovery_orch,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    _append_optimization_warnings,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as final_val_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation_contracts import (  # noqa: E501
    FinalValidationReport,
)


def _fv(**kwargs: object) -> dict[str, object]:
    base = {
        "geometry_valid": True,
        "connectivity_valid": True,
        "overlap_violation_count": 0,
        "quarantined_unrouted_count": 0,
    }
    base.update(kwargs)
    return base


def test_default_validation_recovery_attempts_positive_enables_loop() -> None:
    """Prod defaults: validation retry cap > 0 so timeline may run bounded Pass3→P4 retries."""

    assert fc.MAX_VALIDATION_RECOVERY_ATTEMPTS > fc.RECOVERY_VALIDATION_LOOP_DISABLED
    assert recovery_policy.is_validation_recovery_loop_enabled()


def test_route_validation_recovery_actions_order_and_constants() -> None:
    rpt = FinalValidationReport(
        geometry_valid=False,
        connectivity_valid=False,
        disconnected_stub_count=1,
        quarantined_unrouted_count=2,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=3,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    actions = recovery_orch.route_validation_recovery_actions(rpt)
    assert actions == [
        fc.RECOVERY_ACTION_ROLLBACK_LOWEST_PRIORITY_PLACEMENT,
        fc.RECOVERY_ACTION_PRECALCULATE_REPLACEMENT_ROUTE_SOFT_CORRIDOR,
        fc.RECOVERY_ACTION_ROLLBACK_OR_FAIL_QUARANTINED,
        fc.RECOVERY_ACTION_GEOMETRY_REPAIR_OR_FAIL,
    ]


def test_validation_recovery_allowed_requires_positive_cap() -> None:
    out = {
        "ok": False,
        "return_reason": "validation_connectivity_failed",
        "final_validation": _fv(connectivity_valid=False),
    }
    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 0):
        assert validation_recovery_allowed(out) is False


def test_validation_recovery_allowed_unfinalized_blocked() -> None:
    out = {
        "ok": False,
        "return_reason": "validation_unfinalized_placement_failed",
        "final_validation": _fv(connectivity_valid=False),
    }
    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        assert validation_recovery_allowed(out) is False


def test_validation_recovery_not_triggered_when_ok_true_even_with_quality_warning_tier() -> None:
    """``ok`` True (full solver success): optimization warnings must not enable validation retry."""

    out = {
        "ok": True,
        "return_reason": "ok",
        "final_validation": _fv(
            connectivity_valid=True,
            geometry_valid=True,
            solver_quality_tier=fc.SOLVER_QUALITY_TIER_SUCCESS_VALID_WITH_OPTIMIZATION_WARNING,
            optimization_warnings=[fc.OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE],
        ),
    }
    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        assert validation_recovery_allowed(out) is False


def test_validation_recovery_allowed_connectivity_overlap_quarantine_geometry() -> None:
    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        assert (
            validation_recovery_allowed(
                {
                    "ok": False,
                    "return_reason": "validation_connectivity_failed",
                    "final_validation": _fv(connectivity_valid=False),
                }
            )
            is True
        )
        assert (
            validation_recovery_allowed(
                {
                    "ok": False,
                    "return_reason": "validation_geometry_failed",
                    "final_validation": _fv(overlap_violation_count=1, geometry_valid=True),
                }
            )
            is True
        )
        assert (
            validation_recovery_allowed(
                {
                    "ok": False,
                    "return_reason": "validation_geometry_failed",
                    "final_validation": _fv(quarantined_unrouted_count=1),
                }
            )
            is True
        )
        assert (
            validation_recovery_allowed(
                {
                    "ok": False,
                    "return_reason": "validation_geometry_failed",
                    "final_validation": _fv(geometry_valid=False),
                }
            )
            is True
        )


def test_validation_recovery_allowed_ok_false() -> None:
    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        ok_out = {"ok": True, "return_reason": "ok", "final_validation": _fv()}
        assert validation_recovery_allowed(ok_out) is False


def test_validation_recovery_allowed_missing_stub_blocked() -> None:
    """STEP9 missing-stub geometry cannot be repaired by degraded Pass3→P4 retries."""

    with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", 2):
        assert (
            validation_recovery_allowed(
                {
                    "ok": False,
                    "return_reason": "validation_geometry_failed",
                    "final_validation": _fv(geometry_valid=False, missing_stub_count=2),
                }
            )
            is False
        )


def test_synthesize_recovery_validation_outcome_rollup() -> None:
    s = {
        "return_reason": "validation_connectivity_failed",
        "pass3_rollback_reason": None,
        "p4_reclaim_provisional_commit_rollback_reason": "rb1",
        "pass3_rejected_reason": None,
        "pass3_commit_reason": None,
    }
    synthesize_recovery_validation_outcome(s)
    assert s["recovery_validation_outcome"]["rollback_reason"] == "rb1"
    assert s["recovery_validation_outcome"]["rejected_reason"] == "validation_connectivity_failed"
    assert s["recovery_validation_outcome"]["commit_reason"] is None


def test_synthesize_ok_maps_validation_ok_to_normal_gain() -> None:
    s = {
        "return_reason": "ok",
        "pass3_commit_reason": "validation_ok",
    }
    synthesize_recovery_validation_outcome(s)
    assert s["recovery_validation_outcome"]["commit_reason"] == fc.P3F_COMMIT_REASON_NORMAL_GAIN


def test_synthesize_ok_preserves_semantic_pass3_commit_reason() -> None:
    s = {
        "return_reason": "ok",
        "pass3_commit_reason": fc.COMMIT_REASON_GUARDED_ATOMIC,
    }
    synthesize_recovery_validation_outcome(s)
    assert s["recovery_validation_outcome"]["commit_reason"] == fc.COMMIT_REASON_GUARDED_ATOMIC


def test_synthesize_failure_drops_pass3_commit_reason_from_rollup() -> None:
    s = {
        "return_reason": "validation_connectivity_failed",
        "pass3_commit_reason": fc.P3F_COMMIT_REASON_NORMAL_GAIN,
        "pass3_rejected_reason": None,
    }
    synthesize_recovery_validation_outcome(s)
    assert s["recovery_validation_outcome"]["commit_reason"] is None


def test_finalize_recovery_terminal_reason_post_reclaim_success_via_p4_orchestration() -> None:
    ps = {
        "recovery_trigger_reason": None,
        "p4_orchestration_entry_segment": fc.P4_ORCHESTRATION_ENTRY_SEGMENT_VALUE,
        "post_reclaim_pass3_map_accepted": True,
        "recovery_context_chain": ["a"],
    }
    finalize_recovery_terminal_reason(ps)
    assert ps["recovery_terminal_reason"] == fc.RECOVERY_TERMINAL_POST_RECLAIM_PASS3_SUCCESS


def test_finalize_recovery_terminal_reason_post_reclaim_success() -> None:
    ps = {
        "recovery_trigger_reason": "t",
        "post_reclaim_pass3_map_accepted": True,
        "recovery_context_chain": ["a"],
    }
    finalize_recovery_terminal_reason(ps)
    assert ps["recovery_terminal_reason"] == fc.RECOVERY_TERMINAL_POST_RECLAIM_PASS3_SUCCESS


def test_append_optimization_warnings_above_baseline() -> None:
    s = {"optimization_baseline_internal_transport": 5, "after_internal_transport_count": 7}
    _append_optimization_warnings(s)
    assert s["optimization_warnings"] == [
        fc.OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE
    ]


def test_append_optimization_warnings_no_warning_when_below() -> None:
    s = {"optimization_baseline_internal_transport": 10, "after_internal_transport_count": 3}
    _append_optimization_warnings(s)
    assert s["optimization_warnings"] == []


def _decoded_miners_with_belt_escape_e2e() -> dict:
    entries: list[dict] = []
    for x in range(10, 13):
        entries.append({"X": x, "Y": 0, "T": "Layout_ShapeMiner"})
    for x in range(13, 30):
        entries.append({"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0})
    return {"BP": {"Entries": entries}}


@contextmanager
def _patch_max_validation_recovery_attempts(n: int):
    with patch.object(recovery_orch, "MAX_VALIDATION_RECOVERY_ATTEMPTS", n):
        with patch.object(recovery_policy, "MAX_VALIDATION_RECOVERY_ATTEMPTS", n):
            yield


def _stub_validate_two_phase(
    first: FinalValidationReport,
) -> Callable[[list], FinalValidationReport]:
    state = {"i": 0}

    def _inner(mining_map: list) -> FinalValidationReport:
        state["i"] += 1
        if state["i"] == 1:
            return first
        return final_val_mod.validate_final_mining_layout(mining_map)

    return _inner


def _wrap_validate_first_call_with_mutated_map(
    mutator: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
) -> Callable[[list[dict[str, Any]]], FinalValidationReport]:
    """First finalize: real STEP9 on ``mutator(deepcopy(map))``; later passes: real map."""

    state = {"n": 0}
    real = final_val_mod.validate_final_mining_layout

    def _inner(mining_map: list[dict[str, Any]]) -> FinalValidationReport:
        state["n"] += 1
        if state["n"] == 1:
            return real(mutator(copy.deepcopy(mining_map)))
        return real(mining_map)

    return _inner


def _mutate_overlap_extractor_with_belt(mining_map: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Force ``overlap_violation_count > 0`` (building + transport same cell)."""

    for row in mining_map:
        if row.get("role") != "occupied":
            continue
        if layout_kind(row) not in EXTRACTORS_SHAPE:
            continue
        x, y = row.get("x"), row.get("y")
        if not isinstance(x, int) or not isinstance(y, int) or x == 0:
            continue
        surf = row.get("surface") if isinstance(row.get("surface"), str) else "shape"
        mining_map.append({"x": x, "y": y, "role": "belt", "surface": surf})
        return mining_map
    return mining_map


def _mutate_remove_one_belt_breaking_connectivity(
    mining_map: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Drop a single belt tile until STEP9 reports a connectivity failure (real validator)."""

    real = final_val_mod.validate_final_mining_layout
    m = copy.deepcopy(mining_map)
    belt_idxs = [i for i, r in enumerate(m) if r.get("role") == "belt"]
    for idx in belt_idxs:
        trial = [r for j, r in enumerate(m) if j != idx]
        if not real(trial).connectivity_valid:
            return trial
    msg = "fixture: removing one belt did not break connectivity"
    raise AssertionError(msg)


def _mutate_quarantine_one_extractor(mining_map: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mark one extractor row as quarantined (geometry invalid, real validator)."""

    m = copy.deepcopy(mining_map)
    for i, row in enumerate(m):
        if row.get("role") != "occupied":
            continue
        if layout_kind(row) not in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
            continue
        m[i] = {**row, "placement_state": "quarantined_unrouted"}
        return m
    return m


def _assert_validate_ui_frame_links_validation_recovery(out: dict[str, Any]) -> None:
    timeline = out["solver_timeline"]
    ui_frames = out["solver_replay"]["ui_frames"]
    events = out["solver_replay"]["events"]
    val_i = next(i for i, fr in enumerate(timeline) if fr.get("id") == fc.SOLVER_FRAME_VALIDATE)
    idxs = ui_frames[val_i]["event_indices"]
    vr = fc.RECOVERY_PHASE_VALIDATION_RECOVERY
    assert any(
        isinstance(events[j], dict) and events[j].get("phase") == vr
        for j in idxs
        if isinstance(j, int) and 0 <= j < len(events)
    )


def _run_e2e_real_map_first_validation_fails(
    *,
    mutator: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
    route_spy: list[list[str]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Full pipeline; first finalize STEP9 validates a mutated copy (real validator)."""

    orig_route = recovery_orch.route_validation_recovery_actions

    def _route_wrapped(rpt: FinalValidationReport) -> list[str]:
        actions = orig_route(rpt)
        if route_spy is not None:
            route_spy.append(list(actions))
        return actions

    wrapped = _wrap_validate_first_call_with_mutated_map(mutator)
    with _patch_max_validation_recovery_attempts(2):
        with patch.object(recovery_orch, "route_validation_recovery_actions", _route_wrapped):
            with patch(
                "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                "finalize._validate_final_mining_layout",
                wrapped,
            ):
                with trace_run_scope():
                    return recovery_orch.run_solver_timeline_pipeline(
                        decoded=_decoded_miners_with_belt_escape_e2e(),
                        debug_location="tests.unit.shapez_asteroid.test_recovery_contract",
                        run_id="e2e-validation-recovery-real-map",
                    )


def _run_e2e_with_validate_stub(
    *,
    first_report: FinalValidationReport,
    route_spy: list[list[str]] | None = None,
) -> tuple[dict, dict]:
    """Run full timeline pipeline with STEP9 stubbed on first finalize only."""

    orig_route = recovery_orch.route_validation_recovery_actions

    def _route_wrapped(rpt: FinalValidationReport) -> list[str]:
        actions = orig_route(rpt)
        if route_spy is not None:
            route_spy.append(list(actions))
        return actions

    stub = _stub_validate_two_phase(first_report)
    with _patch_max_validation_recovery_attempts(2):
        with patch.object(recovery_orch, "route_validation_recovery_actions", _route_wrapped):
            with patch(
                "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
                "finalize._validate_final_mining_layout",
                stub,
            ):
                with trace_run_scope():
                    return recovery_orch.run_solver_timeline_pipeline(
                        decoded=_decoded_miners_with_belt_escape_e2e(),
                        debug_location="tests.unit.shapez_asteroid.test_recovery_contract",
                        run_id="e2e-validation-recovery",
                    )


def test_validation_recovery_overlap_routes_action_once() -> None:
    """First STEP9 failure includes overlap → rollback action first; second pass succeeds."""

    first = FinalValidationReport(
        geometry_valid=False,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=2,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    plans: list[list[str]] = []
    out, summary = _run_e2e_with_validate_stub(first_report=first, route_spy=plans)
    assert out["ok"] is True
    assert out["solver_termination"] == "success"
    assert plans[0][0] == fc.RECOVERY_ACTION_ROLLBACK_LOWEST_PRIORITY_PLACEMENT
    assert fc.RECOVERY_ACTION_GEOMETRY_REPAIR_OR_FAIL in plans[0]
    assert summary["validation_recovery_attempts_used"] == 2
    assert summary["validation_recovery_cycles_used"] == 2
    kinds = [e.get("kind") for e in out["solver_replay"].get("events") or []]
    assert kinds.count(solver_replay_ev.SolverMutationEventKind.RECOVERY_BRANCH.value) == 1
    assert isinstance(summary.get("optimization_warnings"), list)
    assert isinstance(out["final_validation"].get("optimization_warnings"), list)


def test_validation_recovery_connectivity_requires_replacement() -> None:
    """Connectivity-only failure maps to replacement-route action (no overlap/quarantine)."""

    first = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=False,
        disconnected_stub_count=1,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    plans: list[list[str]] = []
    out, summary = _run_e2e_with_validate_stub(first_report=first, route_spy=plans)
    assert out["ok"] is True
    assert out["solver_termination"] == "success"
    assert plans[0] == [fc.RECOVERY_ACTION_PRECALCULATE_REPLACEMENT_ROUTE_SOFT_CORRIDOR]
    assert summary["validation_recovery_attempts_used"] == 2


def test_validation_recovery_quarantine_rolls_back_or_terminates() -> None:
    """Quarantine + connectivity failure includes quarantine rollback action after connectivity."""

    first = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=False,
        disconnected_stub_count=0,
        quarantined_unrouted_count=2,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    plans: list[list[str]] = []
    out, summary = _run_e2e_with_validate_stub(first_report=first, route_spy=plans)
    assert out["ok"] is True
    assert plans[0] == [
        fc.RECOVERY_ACTION_PRECALCULATE_REPLACEMENT_ROUTE_SOFT_CORRIDOR,
        fc.RECOVERY_ACTION_ROLLBACK_OR_FAIL_QUARANTINED,
    ]
    assert summary["validation_recovery_attempts_used"] == 2


def test_validation_recovery_attempt_limit_returns_terminal() -> None:
    """With cap 1, two failing finalize cycles stop; no success; one recovery branch."""

    fail = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=False,
        disconnected_stub_count=1,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )

    def _always_fail(_mining_map: list) -> FinalValidationReport:
        return fail

    with _patch_max_validation_recovery_attempts(2):
        with patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
            "finalize._validate_final_mining_layout",
            _always_fail,
        ):
            with trace_run_scope():
                out, summary = recovery_orch.run_solver_timeline_pipeline(
                    decoded=_decoded_miners_with_belt_escape_e2e(),
                    debug_location="tests.unit.shapez_asteroid.test_recovery_contract",
                    run_id="e2e-validation-recovery-fail",
                )
    assert out["ok"] is False
    assert out["return_reason"] == "validation_connectivity_failed"
    assert out["solver_termination"] == "solver_failure"
    assert out["termination"]["tier"] == "SOLVER_FAILURE"
    assert summary["return_reason"] == "validation_connectivity_failed"
    assert summary["solver_termination"] == "solver_failure"
    assert summary["termination"]["tier"] == "SOLVER_FAILURE"
    assert summary["validation_recovery_attempts_used"] == 2
    kinds = [e.get("kind") for e in out["solver_replay"].get("events") or []]
    assert kinds.count(solver_replay_ev.SolverMutationEventKind.RECOVERY_BRANCH.value) == 1


def test_validation_recovery_real_map_overlap_rolls_back_low_priority() -> None:
    """Overlap mutation → real STEP9; first action is rollback_lowest_priority."""

    plans: list[list[str]] = []
    out, summary = _run_e2e_real_map_first_validation_fails(
        mutator=_mutate_overlap_extractor_with_belt,
        route_spy=plans,
    )
    assert out["ok"] is True
    assert plans[0][0] == fc.RECOVERY_ACTION_ROLLBACK_LOWEST_PRIORITY_PLACEMENT
    assert fc.RECOVERY_ACTION_GEOMETRY_REPAIR_OR_FAIL in plans[0]
    assert summary["validation_recovery_attempts_used"] == 2
    kinds = [e.get("kind") for e in out["solver_replay"].get("events") or []]
    assert kinds.count(solver_replay_ev.SolverMutationEventKind.RECOVERY_BRANCH.value) == 1
    _assert_validate_ui_frame_links_validation_recovery(out)


def test_validation_recovery_real_map_connectivity_uses_replacement_first() -> None:
    """Removing one belt breaks connectivity; real report drives replacement-only first plan."""

    plans: list[list[str]] = []
    out, summary = _run_e2e_real_map_first_validation_fails(
        mutator=_mutate_remove_one_belt_breaking_connectivity,
        route_spy=plans,
    )
    assert out["ok"] is True
    assert plans[0] == [fc.RECOVERY_ACTION_PRECALCULATE_REPLACEMENT_ROUTE_SOFT_CORRIDOR]
    assert summary["validation_recovery_attempts_used"] == 2
    kinds = [e.get("kind") for e in out["solver_replay"].get("events") or []]
    assert kinds.count(solver_replay_ev.SolverMutationEventKind.RECOVERY_BRANCH.value) == 1
    _assert_validate_ui_frame_links_validation_recovery(out)


def test_recovery_timeline_envelope_interpretation_fields() -> None:
    """Envelope exposes cap/loop modes so ``0`` is not confused across knobs."""

    env = recovery_orch.recovery_timeline_envelope()
    assert env["total_recovery_cap_mode"] == "unlimited"
    assert env["validation_recovery_loop_mode"] == "enabled"
    assert env["validation_recovery_execution_enabled"] is True


def test_protected_corridors_read_matches_for_reclaim() -> None:
    """P3-B: read variant mirrors write variant for protected reclaim corridors."""

    trace = {"protected_corridors": {"hard": [[1, 0]], "soft": [[2, 0]]}}
    pcs = protected_corridors_for_reclaim(pass3_trace=trace, solver_routing_state=None)
    read = protected_corridors_read_for_reclaim(pass3_trace=trace, solver_routing_state=None)
    assert read.hard == pcs.hard
    assert read.soft == pcs.soft
    assert read.candidate == pcs.existing_layout_hints_cells
    assert read.existing_layout_hints_cells == pcs.existing_layout_hints_cells
    assert read.source == pcs.source


def test_validation_recovery_real_map_quarantine_terminates_or_rolls_back() -> None:
    """Quarantine flag on a real row → geometry invalid; recovery loop repairs then ok."""

    plans: list[list[str]] = []
    out, summary = _run_e2e_real_map_first_validation_fails(
        mutator=_mutate_quarantine_one_extractor,
        route_spy=plans,
    )
    assert out["ok"] is True
    assert fc.RECOVERY_ACTION_ROLLBACK_OR_FAIL_QUARANTINED in plans[0]
    assert fc.RECOVERY_ACTION_GEOMETRY_REPAIR_OR_FAIL in plans[0]
    assert summary["validation_recovery_attempts_used"] == 2
    kinds = [e.get("kind") for e in out["solver_replay"].get("events") or []]
    assert kinds.count(solver_replay_ev.SolverMutationEventKind.RECOVERY_BRANCH.value) == 1
    _assert_validate_ui_frame_links_validation_recovery(out)
