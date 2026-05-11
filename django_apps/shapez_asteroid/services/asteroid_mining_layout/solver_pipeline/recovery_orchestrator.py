"""P5 bounded recovery: validation routing, baselines, optional Pass3→P4 retry loop."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_TOTAL_RECOVERY_ATTEMPTS,
    MAX_VALIDATION_RECOVERY_ATTEMPTS,
    RECOVERY_ACTION_GEOMETRY_REPAIR_OR_FAIL,
    RECOVERY_ACTION_PRECALCULATE_REPLACEMENT_ROUTE_SOFT_CORRIDOR,
    RECOVERY_ACTION_ROLLBACK_LOWEST_PRIORITY_PLACEMENT,
    RECOVERY_ACTION_ROLLBACK_OR_FAIL_QUARANTINED,
    RECOVERY_PHASE_VALIDATION_RECOVERY,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.baseline_routing import (
    compute_shortest_feasible_transport_baseline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_policy import (
    append_recovery_contract_phase,
    apply_recovery_contract_defaults,
    synthesize_recovery_validation_outcome,
    tag_merge_partial_failure_from_step4,
    tag_post_reclaim_pass3_connectivity_break,
    tag_reclaim_incremental_failure_from_summary,
    validation_recovery_allowed,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
    optimization_baseline_internal_transport_pre_step4,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4RoutingResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation_contracts import (  # noqa: E501
    FinalValidationReport,
)

__all__ = [
    "enrich_solver_summary_recovery",
    "optimization_baseline_internal_transport_at_map",
    "optimization_baseline_internal_transport_pre_step4",
    "recovery_timeline_envelope",
    "route_validation_recovery_actions",
    "run_solver_timeline_pipeline",
]


def optimization_baseline_internal_transport_at_map(
    mining_map: list[dict[str, Any]],
    *,
    final_mining_map: list[dict[str, Any]],
) -> int | None:
    """Pass3-compatible internal transport count at a frozen layout (Pass1·Pass2 or STEP4)."""

    return optimization_baseline_internal_transport_pre_step4(
        mining_map, final_mining_map=final_mining_map
    )


def route_validation_recovery_actions(report: FinalValidationReport) -> list[str]:
    """Map STEP9 ``FinalValidationReport`` to ordered recovery action ids (planning only).

    Order: overlap → connectivity → quarantine → geometry. Capacity stays trace-only (STEP9).
    """

    actions: list[str] = []
    if report.overlap_violation_count > 0:
        actions.append(RECOVERY_ACTION_ROLLBACK_LOWEST_PRIORITY_PLACEMENT)
    if not report.connectivity_valid:
        actions.append(RECOVERY_ACTION_PRECALCULATE_REPLACEMENT_ROUTE_SOFT_CORRIDOR)
    if report.quarantined_unrouted_count > 0:
        actions.append(RECOVERY_ACTION_ROLLBACK_OR_FAIL_QUARANTINED)
    if not report.geometry_valid:
        actions.append(RECOVERY_ACTION_GEOMETRY_REPAIR_OR_FAIL)
    return actions


def enrich_solver_summary_recovery(
    summary_fields: dict[str, Any],
    *,
    report: FinalValidationReport,
    step4_result: Step4RoutingResult,
) -> None:
    """Attach P5 recovery fields after ``pass3_summary`` merged into ``summary_fields``."""

    apply_recovery_contract_defaults(summary_fields)
    tag_reclaim_incremental_failure_from_summary(summary_fields)
    tag_post_reclaim_pass3_connectivity_break(summary_fields)
    tag_merge_partial_failure_from_step4(
        summary_fields,
        step4_rolled_back_count=len(step4_result.rolled_back_placement_ids),
        rolled_back_placement_ids=list(step4_result.rolled_back_placement_ids),
        quarantined_placement_ids=list(step4_result.quarantined_placement_ids),
    )

    actions = route_validation_recovery_actions(report)
    summary_fields["recovery_action_plan"] = actions
    if actions:
        append_recovery_contract_phase(summary_fields, RECOVERY_PHASE_VALIDATION_RECOVERY)

    summary_fields["recovery_validation_recovery_eligible"] = bool(actions) and (
        MAX_VALIDATION_RECOVERY_ATTEMPTS > 0
    )
    summary_fields["recovery_bounded_loop_configured"] = (
        MAX_TOTAL_RECOVERY_ATTEMPTS > 0 or MAX_VALIDATION_RECOVERY_ATTEMPTS > 0
    )
    synthesize_recovery_validation_outcome(summary_fields)


def recovery_timeline_envelope() -> dict[str, Any]:
    """Stable metadata for UI / CI: caps and whether a bounded re-run loop is enabled."""

    return {
        "max_total_recovery_attempts": MAX_TOTAL_RECOVERY_ATTEMPTS,
        "max_validation_recovery_attempts": MAX_VALIDATION_RECOVERY_ATTEMPTS,
        "validation_recovery_execution_enabled": MAX_VALIDATION_RECOVERY_ATTEMPTS > 0,
    }


def run_solver_timeline_pipeline(
    *,
    decoded: dict[str, Any],
    debug_location: str,
    run_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Pass12 → STEP4 → (bounded Pass3→P4→finalize loop) mining solver timeline."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.existing_layout_analysis import (  # noqa: E501
        analyze_existing_layout_from_mining_map,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
        solver_mutation_transaction as solver_mut_txn,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
        SolverMutationEventKind,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (  # noqa: E501
        finalize as _finalize_mod,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (  # noqa: E501
        p4_reclaim as _p4_mod,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.pass3 import (
        run_pass3_stage,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.pass12 import (
        run_pass12_stage,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.step4 import (
        run_step4_stage,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        external_predicate_for_mining_map,
    )
    from django_apps.shapez_asteroid.services.blueprint_map_summary import (
        build_map_timeline,
        merge_with_transport_and_final_mining_map,
    )

    replay_events: list[dict[str, Any]] = []
    map_timeline = build_map_timeline(decoded)
    working_map = map_timeline[0]["mining_map"]
    final_map = map_timeline[-1]["mining_map"]
    is_external = external_predicate_for_mining_map(map_timeline[1]["mining_map"])
    step05_baseline_map = merge_with_transport_and_final_mining_map(working_map, final_map)
    existing_layout_analysis = analyze_existing_layout_from_mining_map(
        step05_baseline_map,
        is_external=is_external,
    )

    pass12 = run_pass12_stage(
        working_map=working_map,
        final_map=final_map,
        is_external=is_external,
        existing_layout_analysis=existing_layout_analysis,
        replay_events=replay_events,
        map_timeline=map_timeline,
        debug_location=debug_location,
    )
    step4 = run_step4_stage(
        map_after_pass2=pass12.map_after_pass2,
        final_map=final_map,
        is_external=is_external,
        placement_records=pass12.placement_records,
        pass12_skipped=pass12.pass12_skipped,
        pass12_replay_txn_id=pass12.pass12_replay_txn_id,
        replay_events=replay_events,
        debug_location=debug_location,
        existing_layout_analysis=existing_layout_analysis,
    )
    optimization_baseline_internal_transport = optimization_baseline_internal_transport_at_map(
        pass12.map_after_pass2,
        final_mining_map=final_map,
    )
    optimization_baseline_internal_transport_post_step4 = (
        optimization_baseline_internal_transport_at_map(
            step4.map_after_routing,
            final_mining_map=final_map,
        )
    )
    counterfactual_routing = compute_shortest_feasible_transport_baseline(
        mining_map=pass12.map_after_pass2,
        routing_jobs=None,
        transport_kind=None,
        final_mining_map=final_map,
        is_external=is_external,
    )

    routing_snapshot = solver_mut_txn.copy_mining_map_rows(step4.map_after_routing)
    max_cycles = MAX_VALIDATION_RECOVERY_ATTEMPTS + 1 if MAX_VALIDATION_RECOVERY_ATTEMPTS > 0 else 1
    pass3_recovery_context = False
    out: dict[str, Any] | None = None
    summary_fields: dict[str, Any] | None = None

    for va in range(max_cycles):
        if va > 0:
            replay_events.append(
                {
                    "kind": SolverMutationEventKind.RECOVERY_BRANCH.value,
                    "phase": "validation_recovery",
                    "payload": {"validation_recovery_attempt": va},
                }
            )
        map_for_pass3 = solver_mut_txn.copy_mining_map_rows(routing_snapshot)
        pass3 = run_pass3_stage(
            map_after_routing=map_for_pass3,
            final_map=final_map,
            is_external=is_external,
            pass12_skipped=pass12.pass12_skipped,
            unfinalized_placement_count=step4.unfinalized_placement_count,
            report_step4=step4.report_step4,
            post_step4_counts=step4.post_step4_counts,
            routing_state_summary=step4.routing_state_summary,
            replay_events=replay_events,
            step4_replay_transaction_id=step4.step4_replay_transaction_id,
            pass3_recovery_context=pass3_recovery_context,
            validation_recovery_attempt=va,
            debug_location=debug_location,
        )
        p4 = _p4_mod.run_p4_reclaim_stage(
            map_after_routing=step4.map_after_routing,
            map_final=pass3.map_final,
            final_map=final_map,
            is_external=is_external,
            existing_layout_analysis=existing_layout_analysis,
            eligible_pass3=pass3.eligible_pass3,
            pass3_summary=pass3.pass3_summary,
            p3_trace=pass3.p3_trace,
            step4_result=step4.step4_result,
            step4_replay_transaction_id=step4.step4_replay_transaction_id,
            replay_events=replay_events,
            routing_state_summary=step4.routing_state_summary,
            debug_location=debug_location,
        )
        out, summary_fields = _finalize_mod.build_final_solver_output(
            run_id=run_id,
            map_timeline=map_timeline,
            map_after_pass1=pass12.map_after_pass1,
            map_after_pass2=pass12.map_after_pass2,
            map_after_routing=step4.map_after_routing,
            map_final=p4.map_final,
            pass12_status_fields=pass12.pass12_status_fields,
            pass12_stats=pass12.pass12_stats,
            pass12_phase=pass12.pass12_phase,
            pass12_skipped=pass12.pass12_skipped,
            pre_counts=pass12.pre_counts,
            post_pass2_counts=pass12.post_pass2_counts,
            step4_result=step4.step4_result,
            routing_state_summary=step4.routing_state_summary,
            post_step4_counts=step4.post_step4_counts,
            unfinalized_placement_count=step4.unfinalized_placement_count,
            pass3_summary=p4.pass3_summary,
            existing_layout_analysis=existing_layout_analysis,
            step_hash_step4=step4.step_hash_step4,
            step_hash_pass3=pass3.step_hash_pass3,
            step_hash_p4=p4.step_hash_p4,
            solver_state_hash=p4.solver_state_hash,
            replay_events=replay_events,
            debug_location=debug_location,
            optimization_baseline_internal_transport=optimization_baseline_internal_transport,
            optimization_baseline_internal_transport_post_step4=(
                optimization_baseline_internal_transport_post_step4
            ),
            optimization_counterfactual_internal_transport_sequential_v1=(
                counterfactual_routing.internal_transport_count
            ),
            optimization_counterfactual_failure_reason=counterfactual_routing.failure_reason,
            optimization_counterfactual_aggregation=counterfactual_routing.aggregation,
        )
        assert summary_fields is not None
        if MAX_VALIDATION_RECOVERY_ATTEMPTS > 0:
            c = va + 1
            summary_fields["validation_recovery_cycles_used"] = c
            summary_fields["validation_recovery_attempts_used"] = c
            summary_fields["solver_replay_contract_envelope"] = recovery_timeline_envelope()

        if out.get("ok"):
            break
        if va >= MAX_VALIDATION_RECOVERY_ATTEMPTS:
            break
        if not validation_recovery_allowed(out):
            break
        pass3_recovery_context = True

    assert out is not None and summary_fields is not None
    return out, summary_fields
