"""P5 recovery contract: attempt caps, named phases, and trace-derived failure tags."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_TOTAL_RECOVERY_ATTEMPTS,
    MAX_VALIDATION_RECOVERY_ATTEMPTS,
    RECOVERY_PHASE_MERGE_PARTIAL_FAILURE,
    RECOVERY_PHASE_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK,
    RECOVERY_PHASE_RECLAIM_INCREMENTAL_FAILURE,
)

__all__ = [
    "append_recovery_contract_phase",
    "apply_recovery_contract_defaults",
    "p4_reclaim_cap_blocks_entry",
    "sync_recovery_total_attempts_used_from_chain",
    "tag_merge_partial_failure_from_step4",
    "tag_post_reclaim_pass3_connectivity_break",
    "tag_reclaim_incremental_failure_from_summary",
    "validation_recovery_allowed",
]


def append_recovery_contract_phase(target: dict[str, Any], phase: str) -> None:
    """Append ``phase`` to ``recovery_contract_phases`` if not already last."""

    lst = target.setdefault("recovery_contract_phases", [])
    if not isinstance(lst, list):
        lst = []
        target["recovery_contract_phases"] = lst
    if lst and lst[-1] == phase:
        return
    lst.append(phase)


def apply_recovery_contract_defaults(target: dict[str, Any]) -> None:
    """Ensure P5 recovery summary keys exist (defaults preserve single-pass behaviour)."""

    target.setdefault("recovery_context_chain", [])
    target.setdefault("recovery_contract_phases", [])
    target.setdefault("recovery_total_attempts_used", 0)
    target.setdefault("validation_recovery_attempts_used", 0)
    target.setdefault("max_total_recovery_attempts", MAX_TOTAL_RECOVERY_ATTEMPTS)
    target.setdefault("max_validation_recovery_attempts", MAX_VALIDATION_RECOVERY_ATTEMPTS)
    target.setdefault("recovery_reclaim_incremental_failure", False)
    target.setdefault("recovery_merge_partial_failure", False)
    target.setdefault("recovery_post_reclaim_pass3_connectivity_break", False)
    target.setdefault("recovery_action_plan", [])


def tag_reclaim_incremental_failure_from_summary(pass3_summary: dict[str, Any]) -> None:
    """If P4 incremental route rolled back, set flag + phase (consumes merged P4 trace fields)."""

    if pass3_summary.get("p4_reclaim_incremental_route_rollback_performed"):
        pass3_summary["recovery_reclaim_incremental_failure"] = True
        append_recovery_contract_phase(pass3_summary, RECOVERY_PHASE_RECLAIM_INCREMENTAL_FAILURE)


def tag_merge_partial_failure_from_step4(
    summary: dict[str, Any],
    *,
    step4_rolled_back_count: int,
    rolled_back_placement_ids: list[Any],
) -> None:
    """STEP4 partial rollback / quarantine-style merge failure tagging."""

    if step4_rolled_back_count > 0 or len(rolled_back_placement_ids) > 0:
        summary["recovery_merge_partial_failure"] = True
        append_recovery_contract_phase(summary, RECOVERY_PHASE_MERGE_PARTIAL_FAILURE)


def tag_post_reclaim_pass3_connectivity_break(pass3_summary: dict[str, Any]) -> None:
    """Post-reclaim Pass3 reverted final map → connectivity recovery phase."""

    if pass3_summary.get("post_reclaim_pass3_pass3_reverted"):
        pass3_summary["recovery_post_reclaim_pass3_connectivity_break"] = True
        append_recovery_contract_phase(
            pass3_summary, RECOVERY_PHASE_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK
        )


def p4_reclaim_cap_blocks_entry(pass3_summary: dict[str, Any]) -> bool:
    """True when ``recovery_context_chain`` has reached ``MAX_TOTAL_RECOVERY_ATTEMPTS`` (no P4).

    ``MAX_TOTAL_RECOVERY_ATTEMPTS <= 0`` disables the cap (unlimited).
    """

    if MAX_TOTAL_RECOVERY_ATTEMPTS <= 0:
        return False
    chain = pass3_summary.get("recovery_context_chain")
    if not isinstance(chain, list):
        return False
    return len(chain) >= MAX_TOTAL_RECOVERY_ATTEMPTS


def sync_recovery_total_attempts_used_from_chain(pass3_summary: dict[str, Any]) -> None:
    """Mirror chain length into ``recovery_total_attempts_used`` (replay summary contract)."""

    chain = pass3_summary.get("recovery_context_chain")
    if isinstance(chain, list):
        pass3_summary["recovery_total_attempts_used"] = len(chain)


def validation_recovery_allowed(pipeline_out: dict[str, Any]) -> bool:
    """Whether bounded validation recovery may retry Pass3→P4 with degraded Pass3."""

    if MAX_VALIDATION_RECOVERY_ATTEMPTS <= 0:
        return False
    if pipeline_out.get("ok"):
        return False
    if pipeline_out.get("return_reason") == "validation_unfinalized_placement_failed":
        return False
    fv = pipeline_out.get("final_validation") or {}
    if not fv.get("geometry_valid", True):
        return False
    if int(fv.get("quarantined_unrouted_count") or 0) > 0:
        return False
    if fv.get("connectivity_valid", True):
        return False
    return True
