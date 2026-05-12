"""P5 recovery contract: attempt caps, named phases, and trace-derived failure tags."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    COMMIT_REASON_GUARDED_ATOMIC,
    MAX_TOTAL_RECOVERY_ATTEMPTS,
    MAX_VALIDATION_RECOVERY_ATTEMPTS,
    P3F_COMMIT_REASON_NORMAL_GAIN,
    RECOVERY_PHASE_MERGE_PARTIAL_FAILURE,
    RECOVERY_PHASE_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK,
    RECOVERY_PHASE_RECLAIM_INCREMENTAL_FAILURE,
    RECOVERY_TOTAL_RECOVERY_CAP_UNLIMITED,
    RECOVERY_VALIDATION_LOOP_DISABLED,
)

# §13.5 rollup: ``recovery_validation_outcome.commit_reason`` only (성공 경로).
_ROLLUP_SEMANTIC_COMMIT_REASONS: frozenset[str] = frozenset(
    {
        P3F_COMMIT_REASON_NORMAL_GAIN,
        COMMIT_REASON_GUARDED_ATOMIC,
        "degraded_connected_recovery",
    }
)

__all__ = [
    "append_recovery_contract_phase",
    "apply_recovery_contract_defaults",
    "is_total_recovery_cap_bounded",
    "is_validation_recovery_loop_enabled",
    "p4_reclaim_cap_blocks_entry",
    "sync_recovery_total_attempts_used_from_chain",
    "synthesize_recovery_validation_outcome",
    "tag_merge_partial_failure_from_step4",
    "tag_post_reclaim_pass3_connectivity_break",
    "tag_reclaim_incremental_failure_from_summary",
    "validation_recovery_allowed",
]


def is_validation_recovery_loop_enabled() -> bool:
    """True when Pass3→P4 validation recovery may run more than a single forward pass."""

    return MAX_VALIDATION_RECOVERY_ATTEMPTS > RECOVERY_VALIDATION_LOOP_DISABLED


def is_total_recovery_cap_bounded() -> bool:
    """True when recovery chain length can block P4 (see ``p4_reclaim_cap_blocks_entry``)."""

    return MAX_TOTAL_RECOVERY_ATTEMPTS > RECOVERY_TOTAL_RECOVERY_CAP_UNLIMITED


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
    target.setdefault("p4_orchestration_entry_segment", None)
    target.setdefault("recovery_action_plan", [])
    target.setdefault(
        "recovery_validation_outcome",
        {"commit_reason": None, "rollback_reason": None, "rejected_reason": None},
    )
    target.setdefault("validation_recovery_cycles_used", 0)


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
    quarantined_placement_ids: list[Any] | None = None,
) -> None:
    """STEP4 partial rollback / quarantine-style merge failure tagging."""

    q = quarantined_placement_ids or []
    if step4_rolled_back_count > 0 or len(rolled_back_placement_ids) > 0 or len(q) > 0:
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

    When ``MAX_TOTAL_RECOVERY_ATTEMPTS == RECOVERY_TOTAL_RECOVERY_CAP_UNLIMITED`` (0), the cap
    is off (unlimited chain length for this gate).
    """

    if not is_total_recovery_cap_bounded():
        return False
    chain = pass3_summary.get("recovery_context_chain")
    if not isinstance(chain, list):
        return False
    return len(chain) >= MAX_TOTAL_RECOVERY_ATTEMPTS


def synthesize_recovery_validation_outcome(summary: dict[str, Any]) -> None:
    """Fill ``recovery_validation_outcome`` top-level commit / rollback / rejected summary.

    Per-stage ``pass3_*`` / ``p4_*`` fields stay authoritative; this is a P5 rollup only.
    """

    out: dict[str, Any] = {
        "commit_reason": None,
        "rollback_reason": None,
        "rejected_reason": None,
    }
    rr = str(summary.get("return_reason") or "")

    for key in (
        "pass3_rollback_reason",
        "p4_reclaim_provisional_commit_rollback_reason",
        "p4_reclaim_incremental_route_rollback_reason",
    ):
        v = summary.get(key)
        if v:
            out["rollback_reason"] = str(v)
            break

    for key in (
        "pass3_rejected_reason",
        "p3e3_guarded_commit_rejected_reason",
        "p3e3_guarded_rejected_reason",
        "p4_soft_replace_rejected_reason",
    ):
        v = summary.get(key)
        if v:
            out["rejected_reason"] = str(v)
            break
    if out["rejected_reason"] is None and rr and rr != "ok":
        out["rejected_reason"] = rr

    if rr == "ok":
        cr = summary.get("pass3_commit_reason")
        if cr is None:
            cr_s = ""
        elif isinstance(cr, str):
            cr_s = cr.strip()
        else:
            cr_s = str(cr).strip()
        if cr_s in _ROLLUP_SEMANTIC_COMMIT_REASONS:
            out["commit_reason"] = cr_s
        elif cr_s in {"", "validation_ok"}:
            out["commit_reason"] = P3F_COMMIT_REASON_NORMAL_GAIN
        else:
            out["commit_reason"] = P3F_COMMIT_REASON_NORMAL_GAIN
    else:
        out["commit_reason"] = None

    summary["recovery_validation_outcome"] = out


def sync_recovery_total_attempts_used_from_chain(pass3_summary: dict[str, Any]) -> None:
    """Mirror chain length into ``recovery_total_attempts_used`` (replay summary contract)."""

    chain = pass3_summary.get("recovery_context_chain")
    if isinstance(chain, list):
        pass3_summary["recovery_total_attempts_used"] = len(chain)


def validation_recovery_allowed(pipeline_out: dict[str, Any]) -> bool:
    """Whether bounded validation recovery may retry Pass3→P4 (degraded Pass3 when enabled).

    Capacity is not a STEP9 hard fail; it does not drive this gate (trace / warnings only).
    Unfinalized placements are not recoverable in this loop.
    """

    if not is_validation_recovery_loop_enabled():
        return False
    if pipeline_out.get("ok"):
        return False
    if pipeline_out.get("return_reason") == "validation_unfinalized_placement_failed":
        return False
    fv = pipeline_out.get("final_validation") or {}
    connectivity_ok = bool(fv.get("connectivity_valid", True))
    geometry_ok = bool(fv.get("geometry_valid", True))
    overlap = int(fv.get("overlap_violation_count") or 0)
    quarantine = int(fv.get("quarantined_unrouted_count") or 0)
    if int(fv.get("missing_stub_count") or 0) > 0:
        return False
    if not connectivity_ok:
        return True
    if overlap > 0:
        return True
    if quarantine > 0:
        return True
    if not geometry_ok:
        return True
    return False
