"""P4 reclaim and post-reclaim Pass3 pipeline stage extraction."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    ROUTING_STATE_KEYS_STEP4_HASH,
    SOLVER_FRAME_P4_RECLAIM,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim import (
    reclaim_shadow as p4_shadow,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    solver_mutation_transaction as solver_mut_txn,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_context import (
    RECOVERY_SEGMENT_POST_RECLAIM_PASS3,
    RECOVERY_TRIGGER_POST_PASS3_P4_RECLAIM,
    extend_recovery_chain,
    finalize_recovery_terminal_reason,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_permission import (
    p4_reclaim_permission_snapshot,
    post_reclaim_pass3_gate,
    post_reclaim_pass3_permission,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    SolverMutationEventKind,
    new_replay_transaction_id,
    replay_transaction_payload,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_size_distribution import (  # noqa: E501
    attach_net_internal_transport_saved_after_reclaim,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_state_hash import (
    solver_state_sha256_hex,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
    _internal_transport_count_for_pass3_kind,
    _run_post_reclaim_pass3_once,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    debug_log_event,
    debug_trace_event,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4RoutingResult,
)


@dataclass(frozen=True)
class P4ReclaimStageResult:
    """P4 reclaim 이후 최종 map과 hash."""

    map_final: list[dict[str, Any]]
    pass3_summary: dict[str, Any]
    step_hash_p4: str
    solver_state_hash: str


def run_p4_reclaim_stage(
    *,
    map_after_routing: list[dict[str, Any]],
    map_final: list[dict[str, Any]],
    final_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    existing_layout_analysis: dict[str, Any] | None,
    eligible_pass3: bool,
    pass3_summary: dict[str, Any],
    p3_trace: dict[str, Any],
    step4_result: Step4RoutingResult,
    step4_replay_transaction_id: str | None,
    replay_events: list[dict[str, Any]],
    routing_state_summary: dict[str, Any] | None,
    debug_location: str,
) -> P4ReclaimStageResult:
    """P4 reclaim과 post-reclaim Pass3를 기존 순서대로 실행한다."""

    p3_trace_local: dict[str, Any] = p3_trace if eligible_pass3 else {}
    p4_permission = p4_reclaim_permission_snapshot(
        eligible_pass3=eligible_pass3,
        pass3_summary=pass3_summary,
        pass3_trace=p3_trace_local,
    )
    if not p4_permission["eligible"]:
        p4_trace = p4_shadow.p4_reclaim_shadow_placeholder(
            skip_reason=str(p4_permission["skip_reason"])
        )
    else:
        pass3_summary["recovery_trigger_reason"] = (
            pass3_summary.get("recovery_trigger_reason") or RECOVERY_TRIGGER_POST_PASS3_P4_RECLAIM
        )
        pass3_summary["baseline_internal_transport_at_reclaim_entry"] = (
            _internal_transport_count_for_pass3_kind(
                map_final,
                final_mining_map=final_map,
            )
        )
        solver_rt = p4_shadow.solver_routing_state_for_p4_reclaim(step4_result)
        existing_layout_solver_hints: dict[str, Any] | None = None
        if isinstance(existing_layout_analysis, dict):
            solver_hints = existing_layout_analysis.get("solver_hints")
            if isinstance(solver_hints, dict):
                existing_layout_solver_hints = solver_hints
        p4_txn = solver_mut_txn.SolverMutationTransaction(map_final)
        p4_txn.begin()
        p4_txn_id = new_replay_transaction_id()
        p4_map_before = solver_mut_txn.copy_mining_map_rows(p4_txn.working_map)
        replay_events.append(
            {
                "kind": SolverMutationEventKind.TRANSACTION_BEGIN.value,
                "phase": "p4_reclaim",
                "payload": replay_transaction_payload(
                    transaction_id=p4_txn_id,
                    parent_txn_id=step4_replay_transaction_id,
                ),
            }
        )
        try:
            map_out, p4_trace = p4_shadow.run_p4_reclaim_loop_after_pass3(
                map_after_routing,
                p4_txn.working_map,
                final_mining_map=final_map,
                pass3_trace=p3_trace_local,
                solver_routing_state=solver_rt,
                is_external=is_external,
                existing_layout_solver_hints=existing_layout_solver_hints,
            )
        except BaseException:
            replay_events.append(
                {
                    "kind": SolverMutationEventKind.ROLLBACK.value,
                    "phase": "p4_reclaim",
                    "payload": replay_transaction_payload(
                        transaction_id=p4_txn_id,
                        parent_txn_id=step4_replay_transaction_id,
                    ),
                }
            )
            map_final = p4_txn.rollback()
            raise
        else:
            p4_txn.commit()
            map_final = map_out
            p4_diff = solver_mut_txn.diff_mining_maps(p4_map_before, map_final)
            p4_diff.update(
                replay_transaction_payload(
                    transaction_id=p4_txn_id,
                    parent_txn_id=step4_replay_transaction_id,
                )
            )
            replay_events.append(
                {
                    "kind": SolverMutationEventKind.MAP_DIFF_COMMITTED.value,
                    "phase": "p4_reclaim",
                    "payload": p4_diff,
                }
            )
    pass3_summary.update(p4_trace)
    if post_reclaim_pass3_permission(
        eligible_pass3=eligible_pass3,
        pass3_summary=pass3_summary,
        pass3_trace=p3_trace_local,
    ):
        pass3_summary.setdefault("post_reclaim_pass3_reruns_used", 0)
        do_pr, pr_gate = post_reclaim_pass3_gate(pass3_summary)
        if not do_pr:
            pass3_summary["post_reclaim_pass3_attempted"] = False
            pass3_summary["post_reclaim_pass3_executed"] = False
            pass3_summary["post_reclaim_pass3_ran"] = False
            pass3_summary["post_reclaim_pass3_skip_reason"] = pr_gate
        else:
            map_final, post_reclaim_update = _run_post_reclaim_pass3_once(
                map_final,
                final_mining_map=final_map,
                is_external=is_external,
            )
            pass3_summary.update(post_reclaim_update)
            extend_recovery_chain(pass3_summary, RECOVERY_SEGMENT_POST_RECLAIM_PASS3)
    finalize_recovery_terminal_reason(pass3_summary)
    attach_net_internal_transport_saved_after_reclaim(
        pass3_summary,
        map_final=map_final,
        final_mining_map=final_map,
    )
    step_hash_p4 = solver_state_sha256_hex(
        map_final,
        routing_state=routing_state_summary,
        routing_state_keys=ROUTING_STATE_KEYS_STEP4_HASH,
    )
    debug_log_event(
        debug_location,
        "p4_reclaim_completed",
        {
            "enabled": bool(pass3_summary.get("p4_reclaim_shadow_enabled")),
            "skip_reason": pass3_summary.get("p4_reclaim_shadow_skip_reason"),
            "candidate_count": pass3_summary.get("p4_reclaim_candidate_count"),
            "accepted_count": pass3_summary.get("p4_reclaim_accepted_shadow_count"),
            "provisional_committed": bool(
                pass3_summary.get("p4_reclaim_provisional_commit_committed")
            ),
            "rollback_reason": pass3_summary.get("p4_reclaim_provisional_commit_rollback_reason"),
            "post_reclaim_pass3_skip_reason": pass3_summary.get("post_reclaim_pass3_skip_reason"),
            "baseline_internal_transport_at_reclaim_entry": pass3_summary.get(
                "baseline_internal_transport_at_reclaim_entry"
            ),
            "net_internal_transport_saved_after_reclaim": pass3_summary.get(
                "net_internal_transport_saved_after_reclaim"
            ),
            "post_reclaim_pass3_delta": pass3_summary.get("post_reclaim_pass3_delta"),
            "step_hash_p4": step_hash_p4,
        },
    )
    debug_trace_event(
        debug_location,
        "phase_checkpoint",
        {"phase": "p4", "step_hash_p4": step_hash_p4},
        frame_id=SOLVER_FRAME_P4_RECLAIM,
    )
    return P4ReclaimStageResult(
        map_final=map_final,
        pass3_summary=pass3_summary,
        step_hash_p4=step_hash_p4,
        solver_state_hash=step_hash_p4,
    )
