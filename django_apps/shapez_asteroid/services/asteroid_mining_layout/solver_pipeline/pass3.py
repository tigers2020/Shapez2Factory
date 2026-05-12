"""Pass3 transport minimization pipeline stage extraction."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    RECOVERY_PHASE_VALIDATION_RECOVERY,
    RECOVERY_SEGMENT_VALIDATION_RETRY,
    RECOVERY_TRIGGER_VALIDATION_RECOVERY_ENTRY,
    ROUTING_STATE_KEYS_STEP4_HASH,
    SOLVER_FRAME_PASS3_TRANSPORT,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_f_branch_candidate import (  # noqa: E501
    p3f_pass3_summary_placeholder,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
    p3e2_pass3_summary_placeholder,
    p3e3_pass3_summary_placeholder,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    solver_mutation_transaction as solver_mut_txn,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_context import (
    extend_recovery_chain,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_policy import (
    append_recovery_contract_phase,
    apply_recovery_contract_defaults,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_permission import (
    pass3_permission_snapshot,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    SolverMutationEventKind,
    layout_snapshot_payload,
    new_replay_transaction_id,
    replay_transaction_payload,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_size_distribution import (  # noqa: E501
    attach_pass3_size_distribution,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_state_hash import (
    solver_state_sha256_hex,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    debug_log_event,
    debug_trace_event,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.validation_bridge import (  # noqa: E501
    validate_final_mining_layout_bridge as _validate_final_mining_layout,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    FinalValidationReport,
)


@dataclass(frozen=True)
class Pass3StageResult:
    """Pass3 실행 결과와 P4 입력."""

    map_final: list[dict[str, Any]]
    pass3_summary: dict[str, Any]
    p3_trace: dict[str, Any]
    eligible_pass3: bool
    step_hash_pass3: str


def _run_pass3_transport_minimization_from_maps(
    mining_map: list[dict[str, Any]],
    **kwargs: Any,
) -> tuple[list[dict[str, Any]], Any, dict[str, Any]]:
    """기존 ``solver_service`` patch 지점을 유지하며 Pass3를 호출한다."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
        solver_service,
    )

    return solver_service.run_pass3_transport_minimization_from_maps(mining_map, **kwargs)


def initial_pass3_summary() -> dict[str, Any]:
    """Pass3 기본 summary 계약 필드를 만든다."""

    d: dict[str, Any] = {
        "pass3_skipped": True,
        "pass3_skip_reason": None,
        "pass3_committed": False,
        "pass3_greedy_committed": None,
        "pass3_map_accepted": False,
        "pass3_attempted_commit": False,
        "pass3_final_committed": False,
        "pass3_gain": 0,
        "pass3_reverted": False,
        "before_pass3_counts": None,
        "after_pass3_counts": None,
        "pass3_transport_cells_removed": None,
        "pass3_transport_cells_removed_total": None,
        "before_internal_transport_count": None,
        "after_internal_transport_count": None,
        "pass3_connectivity_reject_sample": None,
        "pass3_greedy_local_replacement": None,
        "recovery_context_chain": [],
        "recovery_trigger": None,
        "recovery_trigger_reason": None,
        "pass3_commit_subtype": None,
        "p4_orchestration_entry_segment": None,
        "recovery_terminal_reason": None,
        **p3e2_pass3_summary_placeholder(rejected_reason="pass3_not_eligible"),
        **p3e3_pass3_summary_placeholder(rejected_reason="pass3_not_eligible"),
        **p3f_pass3_summary_placeholder(rejected_reason="pass3_not_eligible"),
    }
    apply_recovery_contract_defaults(d)
    return d


def run_pass3_stage(
    *,
    map_after_routing: list[dict[str, Any]],
    final_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    pass12_skipped: bool,
    unfinalized_placement_count: int,
    report_step4: FinalValidationReport,
    post_step4_counts: dict[str, int],
    routing_state_summary: dict[str, Any] | None,
    replay_events: list[dict[str, Any]] | None = None,
    step4_replay_transaction_id: str | None = None,
    pass3_recovery_context: bool = False,
    validation_recovery_attempt: int = 0,
    debug_location: str,
    step4_committed: bool,
    step4_trunk_load: dict[str, Any] | None = None,
) -> Pass3StageResult:
    """Pass3 transport minimization을 실행하고 기존 accept/reject 의미를 유지한다."""

    map_final = map_after_routing
    pass3_summary = initial_pass3_summary()
    if validation_recovery_attempt > 0:
        append_recovery_contract_phase(pass3_summary, RECOVERY_PHASE_VALIDATION_RECOVERY)
        extend_recovery_chain(pass3_summary, RECOVERY_SEGMENT_VALIDATION_RETRY)
        pass3_summary["recovery_trigger"] = RECOVERY_TRIGGER_VALIDATION_RECOVERY_ENTRY
    pass3_permission = pass3_permission_snapshot(
        pass12_skipped=pass12_skipped,
        step4_committed=step4_committed,
        unfinalized_placement_count=unfinalized_placement_count,
        report_step4=report_step4,
    )
    eligible_pass3 = bool(pass3_permission["eligible"])
    perm_log = {k: v for k, v in pass3_permission.items() if k != "skip_reason"}
    perm_log["step4_state_source"] = {
        "committed_from": "step4_result",
        "pass3_gate_source": "explicit_arg",
    }
    debug_log_event(
        debug_location,
        "pass3_eligibility_checked",
        perm_log,
    )
    p3_trace: dict[str, Any] = {}
    p3_txn_id: str | None = None
    if eligible_pass3:
        pass3_summary["before_pass3_counts"] = dict(post_step4_counts)
        if replay_events is not None:
            p3_txn_id = new_replay_transaction_id()
            replay_events.append(
                {
                    "kind": SolverMutationEventKind.TRANSACTION_BEGIN.value,
                    "phase": "pass3",
                    "payload": replay_transaction_payload(
                        transaction_id=p3_txn_id,
                        parent_txn_id=step4_replay_transaction_id,
                    ),
                }
            )
            h_before = solver_state_sha256_hex(
                map_after_routing,
                routing_state=routing_state_summary,
                routing_state_keys=ROUTING_STATE_KEYS_STEP4_HASH,
            )
            replay_events.append(
                {
                    "kind": SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value,
                    "phase": "pass3",
                    "payload": layout_snapshot_payload(
                        marker="before",
                        layout_state_sha256=h_before,
                        transaction_id=p3_txn_id,
                        parent_txn_id=step4_replay_transaction_id,
                    ),
                }
            )
        try:
            map_try, _p3_res, p3_trace = _run_pass3_transport_minimization_from_maps(
                map_after_routing,
                final_mining_map=final_map,
                is_external=is_external,
                pass3_recovery_context=pass3_recovery_context,
                trunk_load=step4_trunk_load,
                routing_state_summary=routing_state_summary,
            )
        except BaseException:
            if replay_events is not None and p3_txn_id is not None:
                replay_events.append(
                    {
                        "kind": SolverMutationEventKind.ROLLBACK.value,
                        "phase": "pass3",
                        "payload": replay_transaction_payload(
                            transaction_id=p3_txn_id,
                            parent_txn_id=step4_replay_transaction_id,
                        ),
                    }
                )
            raise
        for k, v in p3_trace.items():
            if (
                k.startswith("p3e2_")
                or k.startswith("p3e3_")
                or k.startswith("p3f_")
                or k == "pass3_greedy_committed"
                or k == "pass3_connectivity_reject_sample"
                or k == "pass3_greedy_local_replacement"
                or k == "pass3_commit_subtype"
            ):
                pass3_summary[k] = v
        if p3_trace.get("pass3_skipped"):
            pass3_summary["pass3_skip_reason"] = p3_trace.get("pass3_skip_reason")
        else:
            report_try = _validate_final_mining_layout(map_try)
            if report_try.geometry_valid and report_try.connectivity_valid:
                map_final = map_try
                upd: dict[str, Any] = {
                    "pass3_skipped": False,
                    "pass3_skip_reason": None,
                    "pass3_committed": bool(p3_trace.get("pass3_committed")),
                    "pass3_attempted_commit": bool(p3_trace.get("pass3_committed")),
                    "pass3_final_committed": True,
                    "pass3_map_accepted": True,
                    "pass3_gain": int(p3_trace.get("gain", 0) or 0),
                    "pass3_bottleneck_count": p3_trace.get("bottleneck_count", 0),
                    "pass3_over_capacity_segments": p3_trace.get("over_capacity_segments", 0),
                }
                if p3_trace.get("pass3_committed"):
                    upd["pass3_commit_reason"] = p3_trace.get("commit_reason")
                else:
                    rejected_reason = p3_trace.get("rejected_reason")
                    if rejected_reason is not None:
                        upd["pass3_rejected_reason"] = rejected_reason
                for k in (
                    "before_transport_count",
                    "after_transport_count",
                    "pass3_transport_cells_removed_total",
                    "pass3_internal_transport_saved",
                    "before_internal_transport_count",
                    "after_internal_transport_count",
                    "pass3_connectivity_reject_sample",
                    "pass3_greedy_local_replacement",
                ):
                    if k in p3_trace:
                        upd[k] = p3_trace[k]
                pass3_summary.update(upd)
            else:
                upd_rev: dict[str, Any] = {
                    "pass3_skipped": False,
                    "pass3_skip_reason": None,
                    "pass3_committed": bool(p3_trace.get("pass3_committed")),
                    "pass3_reverted": True,
                    "pass3_rollback_reason": "final_validation_failed_after_pass3",
                    "pass3_map_accepted": False,
                    "pass3_attempted_commit": bool(p3_trace.get("pass3_committed")),
                    "pass3_final_committed": False,
                    "pass3_gain": int(p3_trace.get("gain", 0) or 0),
                    "pass3_bottleneck_count": p3_trace.get("bottleneck_count", 0),
                    "pass3_over_capacity_segments": p3_trace.get("over_capacity_segments", 0),
                    "pass3_commit_reason": None,
                    "pass3_commit_subtype": None,
                }
                rejected_reason = p3_trace.get("rejected_reason")
                if rejected_reason is not None:
                    upd_rev["pass3_rejected_reason"] = rejected_reason
                pass3_summary.update(upd_rev)
                for k in (
                    "before_transport_count",
                    "after_transport_count",
                    "pass3_transport_cells_removed_total",
                    "pass3_internal_transport_saved",
                    "before_internal_transport_count",
                    "after_internal_transport_count",
                    "pass3_connectivity_reject_sample",
                    "pass3_greedy_local_replacement",
                ):
                    if k in p3_trace:
                        pass3_summary[k] = p3_trace[k]
    elif pass3_permission["skip_reason"] is not None:
        pass3_summary["pass3_skip_reason"] = pass3_permission["skip_reason"]

    if eligible_pass3 and replay_events is not None and p3_txn_id is not None:
        h_after = solver_state_sha256_hex(
            map_final,
            routing_state=routing_state_summary,
            routing_state_keys=ROUTING_STATE_KEYS_STEP4_HASH,
        )
        replay_events.append(
            {
                "kind": SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value,
                "phase": "pass3",
                "payload": layout_snapshot_payload(
                    marker="after",
                    layout_state_sha256=h_after,
                    transaction_id=p3_txn_id,
                    parent_txn_id=step4_replay_transaction_id,
                ),
            }
        )
        if pass3_summary.get("pass3_reverted"):
            replay_events.append(
                {
                    "kind": SolverMutationEventKind.ROLLBACK.value,
                    "phase": "pass3",
                    "payload": replay_transaction_payload(
                        transaction_id=p3_txn_id,
                        parent_txn_id=step4_replay_transaction_id,
                    ),
                }
            )
        else:
            p3_diff = solver_mut_txn.diff_mining_maps(map_after_routing, map_final)
            p3_diff.update(
                replay_transaction_payload(
                    transaction_id=p3_txn_id,
                    parent_txn_id=step4_replay_transaction_id,
                )
            )
            replay_events.append(
                {
                    "kind": SolverMutationEventKind.MAP_DIFF_COMMITTED.value,
                    "phase": "pass3",
                    "payload": p3_diff,
                }
            )

    if eligible_pass3:
        attach_pass3_size_distribution(pass3_summary, map_final=map_final)

    step_hash_pass3 = solver_state_sha256_hex(
        map_final,
        routing_state=routing_state_summary,
        routing_state_keys=ROUTING_STATE_KEYS_STEP4_HASH,
    )
    debug_log_event(
        debug_location,
        "pass3_completed",
        {
            "eligible": eligible_pass3,
            "skipped": bool(pass3_summary.get("pass3_skipped")),
            "skip_reason": pass3_summary.get("pass3_skip_reason"),
            "committed": bool(pass3_summary.get("pass3_committed")),
            "greedy_committed": pass3_summary.get("pass3_greedy_committed"),
            "guarded_committed": bool(pass3_summary.get("p3e3_guarded_committed") or False),
            "map_accepted": bool(pass3_summary.get("pass3_map_accepted")),
            "final_committed": bool(pass3_summary.get("pass3_final_committed")),
            "reverted": bool(pass3_summary.get("pass3_reverted")),
            "gain": pass3_summary.get("pass3_gain", 0),
            "before_counts": pass3_summary.get("before_pass3_counts"),
            "after_counts": pass3_summary.get("after_pass3_counts"),
            "step_hash_pass3": step_hash_pass3,
        },
    )
    debug_trace_event(
        debug_location,
        "phase_checkpoint",
        {"phase": "pass3", "step_hash_pass3": step_hash_pass3},
        frame_id=SOLVER_FRAME_PASS3_TRANSPORT,
    )
    return Pass3StageResult(
        map_final=map_final,
        pass3_summary=pass3_summary,
        p3_trace=p3_trace,
        eligible_pass3=eligible_pass3,
        step_hash_pass3=step_hash_pass3,
    )
