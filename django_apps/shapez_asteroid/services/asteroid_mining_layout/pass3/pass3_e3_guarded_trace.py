"""P3-E3 guarded trace payloads and placeholders."""

from __future__ import annotations

import math
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_ROUTE_LENGTH_RATIO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded_dto import (
    P3E3GuardedCommitCandidate,
    P3E3GuardedPrecheckCandidate,
    p3e3_guarded_commit_candidate_as_trace_dict,
    p3e3_guarded_precheck_candidate_as_trace_dict,
)


def _p3e3_precheck_top_level_reason(*, shadow_trace: dict[str, Any]) -> str:
    """Single ``p3e3_guarded_rejected_reason`` string for precheck (deferral or shadow-derived)."""

    if not shadow_trace.get("p3e2_shadow_enabled"):
        return "precheck_shadow_disabled"
    if shadow_trace.get("p3e2_shadow_would_commit"):
        return "precheck_ok_pending_atomic_commit"
    sr = shadow_trace.get("p3e2_shadow_rejected_reason")
    if isinstance(sr, str) and sr:
        return f"precheck_shadow_{sr}"
    return "precheck_shadow_unknown"


def _p3e3_atomic_trace_disabled() -> dict[str, Any]:
    """Trace keys when P3-E3b atomic phase does not run (guarded off or early return)."""

    return {
        "p3e3_atomic_candidate_built": None,
        "p3e3_candidate_validation_passed": None,
        "p3e3_guarded_commit_would_accept": None,
        "p3e3_guarded_commit_committed": None,
        "p3e3_guarded_commit_rejected_reason": None,
        "p3e3_guarded_commit_candidate": None,
        "p3e3_guarded_commit_rollback_performed": None,
        "p3e3_guarded_commit_rollback_reason": None,
        "p3e3_guarded_commit_mode": None,
        "p3e3_guarded_known_good_transport_cell_count": None,
        "p3e3_guarded_post_commit_validation_passed": None,
        "p3e3_route_length_ratio_cap": None,
        "p3e3_route_allowed_max_length": None,
        "p3e3_route_length_slack_cells": None,
    }


def _p3e3_atomic_trace_from_dto(
    dto: P3E3GuardedCommitCandidate,
    *,
    atomic_candidate_built: bool,
    validation_passed: bool,
    would_accept: bool,
    atomic_rejected: str | None,
    route_length_ratio_cap: float | None = None,
) -> dict[str, Any]:
    """P3-E3 atomic candidate DTO를 trace-friendly dict로 변환한다 (§11.3 guarded commit)."""
    cap = float(
        MAX_ROUTE_LENGTH_RATIO if route_length_ratio_cap is None else route_length_ratio_cap
    )
    allowed_max: int | None = None
    slack: int | None = None
    bl = dto.baseline_route_length
    cl = dto.candidate_route_length
    if bl is not None and int(bl) > 0 and cl is not None:
        allowed_max = int(math.ceil(float(bl) * cap))
        slack = int(allowed_max) - int(cl)
    return {
        "p3e3_atomic_candidate_built": atomic_candidate_built,
        "p3e3_candidate_validation_passed": validation_passed,
        "p3e3_guarded_commit_would_accept": would_accept,
        "p3e3_guarded_commit_committed": False,
        "p3e3_guarded_commit_rejected_reason": atomic_rejected,
        "p3e3_guarded_commit_candidate": p3e3_guarded_commit_candidate_as_trace_dict(dto),
        "p3e3_guarded_commit_rollback_performed": False,
        "p3e3_guarded_commit_rollback_reason": None,
        "p3e3_guarded_commit_mode": None,
        "p3e3_guarded_known_good_transport_cell_count": None,
        "p3e3_guarded_post_commit_validation_passed": None,
        "p3e3_route_length_ratio_cap": cap,
        "p3e3_route_allowed_max_length": allowed_max,
        "p3e3_route_length_slack_cells": slack,
    }


def p3e3_emit_guarded_trace(
    *,
    guarded_enabled: bool,
    shadow_trace: dict[str, Any],
    outlet_stub_cells: tuple[Coord, ...],
) -> dict[str, Any]:
    """P3-E3a: trace-only precheck + candidate DTO; never sets ``p3e3_guarded_committed``."""

    if not guarded_enabled:
        return {
            "p3e3_guarded_commit_enabled": False,
            "p3e3_guarded_commit_attempted": False,
            "p3e3_guarded_committed": False,
            "p3e3_guarded_rejected_reason": "guarded_disabled",
            "p3e3_guarded_precheck_candidate": None,
            "p3e3_guarded_precheck_shadow_rejected_reason": None,
            **_p3e3_atomic_trace_disabled(),
        }

    sr_raw = shadow_trace.get("p3e2_shadow_rejected_reason")
    sr_clean: str | None = sr_raw if isinstance(sr_raw, str) else None

    cand = P3E3GuardedPrecheckCandidate(
        outlet_stub_cells=outlet_stub_cells,
        lex_internal_transport_count=int(
            shadow_trace.get("p3e2_lex_internal_transport_count") or 0
        ),
        lex_path_length_sum=int(shadow_trace.get("p3e2_lex_path_length") or 0),
        greedy_internal_transport_count=int(
            shadow_trace.get("p3e2_greedy_internal_transport_count") or 0
        ),
        greedy_path_length_sum=int(shadow_trace.get("p3e2_greedy_path_length") or 0),
        lex_all_found=bool(shadow_trace.get("p3e2_lex_found")),
        shadow_would_commit_preview=bool(shadow_trace.get("p3e2_shadow_would_commit")),
        shadow_rejected_reason=sr_clean,
        lex_success_count=int(shadow_trace.get("p3e2_lex_success_count") or 0),
        greedy_success_count=int(shadow_trace.get("p3e2_greedy_success_count") or 0),
    )
    return {
        "p3e3_guarded_commit_enabled": True,
        "p3e3_guarded_commit_attempted": True,
        "p3e3_guarded_committed": False,
        "p3e3_guarded_rejected_reason": _p3e3_precheck_top_level_reason(shadow_trace=shadow_trace),
        "p3e3_guarded_precheck_candidate": p3e3_guarded_precheck_candidate_as_trace_dict(cand),
        "p3e3_guarded_precheck_shadow_rejected_reason": shadow_trace.get(
            "p3e2_shadow_rejected_reason"
        ),
        **_p3e3_atomic_trace_disabled(),
    }


def p3e3_pass3_summary_placeholder(*, rejected_reason: str | None) -> dict[str, Any]:
    """Stable ``p3e3_*`` keys when Pass3 guarded-commit path does not run."""

    return {
        "p3e3_guarded_commit_enabled": None,
        "p3e3_guarded_commit_attempted": None,
        "p3e3_guarded_committed": None,
        "p3e3_guarded_rejected_reason": rejected_reason,
        "p3e3_guarded_precheck_candidate": None,
        "p3e3_guarded_precheck_shadow_rejected_reason": None,
        "p3e3_atomic_candidate_built": None,
        "p3e3_candidate_validation_passed": None,
        "p3e3_guarded_commit_would_accept": None,
        "p3e3_guarded_commit_committed": None,
        "p3e3_guarded_commit_rejected_reason": None,
        "p3e3_guarded_commit_candidate": None,
        "p3e3_guarded_commit_rollback_performed": None,
        "p3e3_guarded_commit_rollback_reason": None,
        "p3e3_guarded_commit_mode": None,
        "p3e3_guarded_known_good_transport_cell_count": None,
        "p3e3_guarded_post_commit_validation_passed": None,
        "p3e3_route_length_ratio_cap": None,
        "p3e3_route_allowed_max_length": None,
        "p3e3_route_length_slack_cells": None,
    }


def p3e2_pass3_summary_placeholder(*, rejected_reason: str) -> dict[str, Any]:
    """Stable ``p3e2_*`` keys when Pass3 or shadow does not run (solver timeline / early skip)."""

    return {
        "p3e2_shadow_enabled": None,
        "p3e2_lex_found": None,
        "p3e2_lex_internal_transport_count": None,
        "p3e2_lex_path_length": None,
        "p3e2_greedy_internal_transport_count": None,
        "p3e2_greedy_path_length": None,
        "p3e2_shadow_would_commit": False,
        "p3e2_shadow_rejected_reason": rejected_reason,
        "p3e2_outlet_count": None,
        "p3e2_lex_success_count": None,
        "p3e2_greedy_success_count": None,
        "p3e2_hard_protected_guard_state": None,
    }
