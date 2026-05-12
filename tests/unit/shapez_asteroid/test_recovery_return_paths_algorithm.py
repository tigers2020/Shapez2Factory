"""§4.3 recovery return paths: invariants vs Algorithm (regression, not snapshots)."""

from __future__ import annotations

import inspect
from typing import Any
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import recovery_policy
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


def test_recovery_orchestrator_calls_step4_once() -> None:
    """§4.3 / §11: bounded validation recovery does not re-enter STEP4."""

    src = inspect.getsource(ro.run_solver_timeline_pipeline)
    assert src.count("run_step4_stage(") == 1
