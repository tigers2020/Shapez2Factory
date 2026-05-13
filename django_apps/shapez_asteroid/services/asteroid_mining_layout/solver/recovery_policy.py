"""P5 recovery contract: attempt caps, named phases, and trace-derived failure tags.

Algorithm §4.3 canonical return-path rows (spec only): ``solver.recovery_return_policy``;
orchestrator alignment is D2-B/C.
"""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_TOTAL_RECOVERY_ATTEMPTS,
    MAX_VALIDATION_RECOVERY_ATTEMPTS,
    PASS3_GREEDY_REJECT_DETAIL_CONNECTIVITY,
    RECOVERY_PHASE_MERGE_PARTIAL_FAILURE,
    RECOVERY_PHASE_PASS3_CONNECTIVITY_BREAK,
    RECOVERY_PHASE_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK,
    RECOVERY_PHASE_RECLAIM_INCREMENTAL_FAILURE,
    RECOVERY_TOTAL_RECOVERY_CAP_UNLIMITED,
    RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK,
    RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK,
    RECOVERY_TRIGGER_RECLAIM_INCREMENTAL_FAILURE,
    RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE,
    RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
    RECOVERY_VALIDATION_LOOP_DISABLED,
    ROLLUP_COMMIT_REASONS_CANONICAL,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.semantic_contracts import (
    partition_pass3_commit_reason_payload,
    rollup_return_reason_to_recovery_trigger,
)

__all__ = [
    "append_recovery_contract_phase",
    "append_recovery_return_policy_trace_entries",
    "apply_recovery_contract_defaults",
    "is_total_recovery_cap_bounded",
    "is_validation_recovery_loop_enabled",
    "p4_reclaim_cap_blocks_entry",
    "step9_reports_hard_invariant_failure_for_bounded_recovery",
    "sync_recovery_total_attempts_used_from_chain",
    "synthesize_recovery_validation_outcome",
    "tag_merge_partial_failure_from_step4",
    "tag_pass3_connectivity_break_from_greedy_trace",
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
    target.setdefault("recovery_pass3_connectivity_break", False)
    target.setdefault("recovery_post_reclaim_pass3_connectivity_break", False)
    target.setdefault("p4_orchestration_entry_segment", None)
    target.setdefault("recovery_action_plan", [])
    target.setdefault("recovery_trigger", None)
    target.setdefault("pass3_commit_subtype", None)
    target.setdefault(
        "recovery_validation_outcome",
        {
            "commit_reason": None,
            "rollback_reason": None,
            "rejected_reason": None,
            "recovery_trigger": None,
            "recovery_trigger_parallel": None,
            "pass3_commit_subtype": None,
        },
    )
    target.setdefault("validation_recovery_cycles_used", 0)
    target.setdefault("total_recovery_attempts_used", 0)
    target.setdefault("total_recovery_attempts", 0)
    target.setdefault("validation_recovery_attempts", 0)
    target.setdefault("post_reclaim_pass3_reruns_lifetime_used", 0)
    target.setdefault("recovery_trigger_parallel", [])


def append_recovery_return_policy_trace_entries(summary: dict[str, Any]) -> None:
    """Attach §4.3 ``recovery_return_policy`` row snapshots for active flags (trace-only).

    Does not branch the pipeline; mirrors ``recovery_return_policy_for_trigger`` for CI/UI.
    """

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
        recovery_return_policy as _rrp,
    )

    entries: list[dict[str, Any]] = []

    def _add(trigger: str) -> None:
        pol = _rrp.recovery_return_policy_for_trigger(trigger)
        entries.append(
            {
                "recovery_trigger": trigger,
                "policy_id": pol.policy_id.value,
                "primary_return_steps": list(pol.primary_return_steps),
                "reenters_step4": pol.reenters_step4,
            }
        )

    if summary.get("recovery_pass3_connectivity_break"):
        _add(RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK)
    if summary.get("recovery_reclaim_incremental_failure"):
        _add(RECOVERY_TRIGGER_RECLAIM_INCREMENTAL_FAILURE)
    if summary.get("recovery_post_reclaim_pass3_connectivity_break"):
        _add(RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK)
    st4 = summary.get("step4_recovery_trigger")
    if st4 == RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE:
        _add(RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE)
    elif st4 == RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE:
        _add(RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE)
    if entries:
        summary["recovery_return_policy_trace"] = entries


def tag_pass3_connectivity_break_from_greedy_trace(
    pass3_summary: dict[str, Any],
    p3_trace: dict[str, Any],
    *,
    validation_recovery_attempt: int,
) -> None:
    """Greedy Pass3 connectivity-only reject (§4.3.1): flag + bounded trigger for return-policy."""

    if validation_recovery_attempt > 0:
        return
    if p3_trace.get("pass3_skipped"):
        return
    if p3_trace.get("pass3_connectivity_reject_sample") is None:
        return
    detail = str(p3_trace.get("pass3_greedy_reject_detail") or "")
    if detail != PASS3_GREEDY_REJECT_DETAIL_CONNECTIVITY:
        return
    pass3_summary["recovery_pass3_connectivity_break"] = True
    if not str(pass3_summary.get("recovery_trigger") or "").strip():
        pass3_summary["recovery_trigger"] = RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK
    append_recovery_contract_phase(pass3_summary, RECOVERY_PHASE_PASS3_CONNECTIVITY_BREAK)


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

    if not pass3_summary.get("post_reclaim_pass3_pass3_reverted"):
        return
    pass3_summary["recovery_post_reclaim_pass3_connectivity_break"] = True
    if pass3_summary.get("recovery_reclaim_incremental_failure"):
        pl = pass3_summary.setdefault("recovery_trigger_parallel", [])
        if RECOVERY_TRIGGER_RECLAIM_INCREMENTAL_FAILURE not in pl:
            pl.append(RECOVERY_TRIGGER_RECLAIM_INCREMENTAL_FAILURE)
    pass3_summary["recovery_trigger"] = RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK
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
    ``commit_reason`` is §13.5 success classification only (``pass3_final_committed``).
    ``recovery_trigger`` mirrors bounded recovery entry (not P4 orchestration markers).
    """

    out: dict[str, Any] = {
        "commit_reason": None,
        "rollback_reason": None,
        "rejected_reason": None,
        "recovery_trigger": None,
        "recovery_trigger_parallel": None,
        "pass3_commit_subtype": None,
    }
    rr = str(summary.get("return_reason") or "")

    rt = summary.get("recovery_trigger")
    if rt is not None and str(rt).strip():
        out["recovery_trigger"] = str(rt).strip()
    elif summary.get("recovery_post_reclaim_pass3_connectivity_break"):
        out["recovery_trigger"] = RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK
    par = summary.get("recovery_trigger_parallel")
    if isinstance(par, list) and par:
        out["recovery_trigger_parallel"] = [str(x) for x in par]

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

    st = summary.get("pass3_commit_subtype")
    if st is not None and str(st).strip():
        out["pass3_commit_subtype"] = str(st).strip()

    if not (out.get("recovery_trigger") or "").strip() and rr and rr != "ok":
        mapped_rt = rollup_return_reason_to_recovery_trigger(rr)
        if mapped_rt is not None:
            out["recovery_trigger"] = mapped_rt

    cr_commit, _promoted = partition_pass3_commit_reason_payload(
        summary.get("pass3_commit_reason"),
        pass3_committed=bool(summary.get("pass3_committed")),
        pass3_final_committed=bool(summary.get("pass3_final_committed")),
    )
    if (
        rr == "ok"
        and bool(summary.get("pass3_final_committed"))
        and bool(summary.get("pass3_committed"))
        and cr_commit in ROLLUP_COMMIT_REASONS_CANONICAL
    ):
        out["commit_reason"] = cr_commit

    summary["recovery_validation_outcome"] = out


def sync_recovery_total_attempts_used_from_chain(pass3_summary: dict[str, Any]) -> None:
    """Mirror chain length into recovery attempt counters (replay summary contract).

    ``total_recovery_attempts_used`` tracks ``recovery_context_chain`` only — STEP4
    ``cascade_corrective_attempts`` are separate and must not increment this counter.
    """

    chain = pass3_summary.get("recovery_context_chain")
    if isinstance(chain, list):
        n = len(chain)
        pass3_summary["recovery_total_attempts_used"] = n
        pass3_summary["total_recovery_attempts_used"] = n


def step9_reports_hard_invariant_failure_for_bounded_recovery(
    final_validation: dict[str, Any] | None,
) -> bool:
    """True when STEP9 ``final_validation`` fields indicate a bounded Pass3→P4 retry may apply.

    Algorithm §15: validation recovery reacts to STEP9 **hard invariant** signals only.
    Optimization / quality tiers are carried on ``solver_summary`` and must not flip this
    predicate alone. Missing-stub geometry is treated as non-recoverable in this loop
    (degraded Pass3 cannot invent stubs).
    """

    fv = final_validation if isinstance(final_validation, dict) else {}
    connectivity_ok = bool(fv.get("connectivity_valid", True))
    geometry_ok = bool(fv.get("geometry_valid", True))
    overlap = int(fv.get("overlap_violation_count") or 0)
    quarantine = int(fv.get("quarantined_unrouted_count") or 0)
    if int(fv.get("missing_stub_count") or 0) > 0:
        return False
    if int(fv.get("fixed_output_stub_removed_count") or 0) > 0:
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


def validation_recovery_allowed(pipeline_out: dict[str, Any]) -> bool:
    """Whether bounded validation recovery may retry Pass3→P4 (degraded Pass3 when enabled).

    Algorithm §11 / §15: recovery is Pass3→P4→finalize only (no STEP4 re-entry for **final
    validation** failure). ``step4_routing_failure`` bounded STEP4 retries and the no-loop gate
    live in :func:`run_solver_timeline_pipeline`. Capacity is not a STEP9 hard fail here.
    Unfinalized placements are not recoverable in this loop. ``ok`` False from partial success
    with a STEP9-clean report does not enable retry (see
    :func:`step9_reports_hard_invariant_failure_for_bounded_recovery`).
    """

    if not is_validation_recovery_loop_enabled():
        return False
    if pipeline_out.get("ok"):
        return False
    if pipeline_out.get("return_reason") == "validation_unfinalized_placement_failed":
        return False
    fv = pipeline_out.get("final_validation") or {}
    return step9_reports_hard_invariant_failure_for_bounded_recovery(fv)
