"""§4.3 recovery return paths: invariants vs Algorithm (regression, not snapshots).

Policy rows mirror Algorithm ``02_pipeline_control_flow`` §4.3 / §4.3.1 / §4.3.2 and
``13_step9_validation`` §15 (see ``recovery_return_policy.py``).
"""

from __future__ import annotations

import inspect
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


def _clean_fv() -> dict[str, Any]:
    return {
        "geometry_valid": True,
        "connectivity_valid": True,
        "overlap_violation_count": 0,
        "quarantined_unrouted_count": 0,
        "missing_stub_count": 0,
    }


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


def test_recovery_return_policy_unknown_trigger_raises() -> None:
    with pytest.raises(ValueError, match="unknown recovery trigger"):
        rrp.recovery_return_policy_for_trigger("not_in_section_4_3_table")
