"""Final validation, frame assembly, and summary contract helpers."""

from __future__ import annotations

from typing import Any

from django.conf import settings

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_TOTAL_RECOVERY_ATTEMPTS,
    MAX_VALIDATION_RECOVERY_ATTEMPTS,
    OPTIMIZATION_BASELINE_SNAPSHOT_PASS1_PASS2_PRE_STEP4,
    OPTIMIZATION_QUALITY_RATIO_WARN_THRESHOLD,
    OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE,
    OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_QUALITY_RATIO_HIGH,
    SOLVER_FRAME_INIT,
    SOLVER_FRAME_PASS1_OUTER,
    SOLVER_FRAME_PASS2_INTERNAL,
    SOLVER_FRAME_PASS3_TRANSPORT,
    SOLVER_FRAME_STEP4_ROUTING,
    SOLVER_FRAME_VALIDATE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.spatial_authority import (  # noqa: E501
    assert_protected_corridors_agree_with_transport_map,
    infer_transport_kind_from_mining_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTENSIONS,
    layout_kind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.metrics_contract import (
    OPTIMIZATION_REPLAY_METRIC_KEYS,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_corridors import (  # noqa: E501
    protected_corridors_overlay_from_routing_state,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    build_solver_replay_snapshot,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_size_distribution import (  # noqa: E501
    removed_counts_distribution,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
    _placement_candidate_blocked_count_from_pass12,
    _solver_stats_by_prefix,
    count_layout_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    debug_log_event,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.recovery_orchestrator import (  # noqa: E501
    enrich_solver_summary_recovery,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4RoutingResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.trunk_load_observation_soft import (  # noqa: E501
    trunk_load_observation_soft_warnings,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import (
    merge_with_transport_and_final_mining_map,
)


def _validate_final_mining_layout(mining_map: list[dict[str, Any]]) -> Any:
    """기존 ``solver_service`` validation patch 지점을 유지한다."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
        solver_service,
    )

    return solver_service.validate_final_mining_layout(mining_map)


def _append_optimization_warnings(summary_fields: dict[str, Any]) -> None:
    """Compare Pass1·Pass2 baseline internal transport to final Pass3 count (P5 summary)."""

    warnings: list[str] = []
    baseline = summary_fields.get("optimization_baseline_internal_transport")
    after = summary_fields.get("after_internal_transport_count")
    if isinstance(baseline, int) and isinstance(after, int) and after > baseline:
        warnings.append(OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE)
    ratio = summary_fields.get("optimization_internal_transport_quality_ratio")
    if isinstance(ratio, (int, float)) and float(ratio) > OPTIMIZATION_QUALITY_RATIO_WARN_THRESHOLD:
        warnings.append(OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_QUALITY_RATIO_HIGH)
    summary_fields["optimization_warnings"] = warnings


def _baseline_extension_count(mining_map: list[dict[str, Any]]) -> int:
    n = 0
    for row in mining_map:
        if row.get("role") != "occupied":
            continue
        layout_kind_value = layout_kind(row)
        if layout_kind_value in EXTENSIONS:
            n += 1
    return n


def _protected_corridor_counts_from_routing_state(
    routing_state: dict[str, Any] | None,
) -> tuple[int, int, int]:
    """Return (hard_n, soft_n, pool_len) for §14.4 ``before_return_validate`` trace."""

    if not isinstance(routing_state, dict):
        return 0, 0, 0
    hard = routing_state.get("hard_protected_corridors")
    soft = routing_state.get("soft_protected_corridors")
    hard_count = len(hard) if isinstance(hard, list) else 0
    soft_count = len(soft) if isinstance(soft, list) else 0
    return hard_count, soft_count, hard_count + soft_count


def build_final_solver_output(
    *,
    run_id: str,
    map_timeline: list[dict[str, Any]],
    map_after_pass1: list[dict[str, Any]],
    map_after_pass2: list[dict[str, Any]],
    map_after_routing: list[dict[str, Any]],
    map_final: list[dict[str, Any]],
    pass12_status_fields: dict[str, Any],
    pass12_stats: dict[str, Any],
    pass12_phase: str,
    pass12_skipped: bool,
    pre_counts: dict[str, int],
    post_pass2_counts: dict[str, int],
    step4_result: Step4RoutingResult,
    routing_state_summary: dict[str, Any] | None,
    post_step4_counts: dict[str, int],
    unfinalized_placement_count: int,
    pass3_summary: dict[str, Any],
    existing_layout_analysis: dict[str, Any] | None,
    step_hash_step4: str | None,
    step_hash_pass3: str | None,
    step_hash_p4: str | None,
    solver_state_hash: str | None,
    replay_events: list[dict[str, Any]],
    debug_location: str,
    optimization_baseline_internal_transport: int | None = None,
    optimization_baseline_internal_transport_post_step4: int | None = None,
    optimization_counterfactual_internal_transport_sequential_v1: int | None = None,
    optimization_counterfactual_failure_reason: str | None = None,
    optimization_counterfactual_aggregation: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """최종 validation, summary, timeline, replay payload를 기존 schema로 조립한다."""

    report = _validate_final_mining_layout(map_final)
    post_routing_counts = count_layout_cells(map_final)
    layout_ok = report.geometry_valid and report.connectivity_valid
    if unfinalized_placement_count > 0:
        return_reason = "validation_unfinalized_placement_failed"
    elif layout_ok:
        return_reason = "ok"
    elif not report.geometry_valid:
        return_reason = "validation_geometry_failed"
    else:
        return_reason = "validation_connectivity_failed"

    step4_rollback_count = len(step4_result.rolled_back_placement_ids)
    broken_routed_n = int(step4_result.trunk_load.get("broken_routed_route_count", 0) or 0)
    cascade_rb_n = int(step4_result.trunk_load.get("cascade_rollback_count", 0) or 0)
    layout_degraded = (
        (not layout_ok)
        or unfinalized_placement_count > 0
        or step4_rollback_count > 0
        or broken_routed_n > 0
        or cascade_rb_n > 0
    )
    summary_geometry_valid = report.geometry_valid and unfinalized_placement_count == 0

    if getattr(settings, "SHAPEZ_MINING_ASSERT_STEP9_ROUTING_STATE", False):
        assert_protected_corridors_agree_with_transport_map(
            routing_state_summary,
            map_final,
            transport_kind=infer_transport_kind_from_mining_map(map_final),
            context="pre_return_step9",
        )

    hard_pc, soft_pc, pool_pc = _protected_corridor_counts_from_routing_state(routing_state_summary)
    _pc_overlay_brv = protected_corridors_overlay_from_routing_state(routing_state_summary)
    _cand_n = int((_pc_overlay_brv.get("counts") or {}).get("candidate") or 0)
    before_return_validate: dict[str, Any] = {
        "extractor_count": report.extractor_count,
        "extension_count": report.extension_count,
        "baseline_after_pass2_extensions": _baseline_extension_count(map_after_pass2),
        "protected_corridor_pool_len": pool_pc,
        "hard_protected_count": hard_pc,
        "soft_protected_count": soft_pc,
        "candidate_protected_corridor_count": _cand_n,
        "transport_connected": report.transport_connectivity_ok,
    }

    pass12_trace_fields = {k: v for k, v in pass12_stats.items() if k != "placement_records"}
    debug_log_event(
        debug_location,
        "final_validation_completed",
        {
            "return_reason": return_reason,
            "layout_ok": layout_ok,
            "geometry_valid": summary_geometry_valid,
            "connectivity_valid": report.connectivity_valid,
            "disconnected_stub_count": report.disconnected_stub_count,
            "orphan_transport_count": report.orphan_transport_count,
            "overlap_violation_count": report.overlap_violation_count,
            "missing_stub_count": report.missing_stub_count,
            "unfinalized_placement_count": unfinalized_placement_count,
            "final_counts": post_routing_counts,
        },
    )
    removed = removed_counts_distribution(
        before_counts=pre_counts,
        after_counts=post_pass2_counts,
    )
    summary_fields = {
        "run_id": run_id,
        "return_reason": return_reason,
        "after_pass2_baseline_counts": post_pass2_counts,
        "final_counts": post_routing_counts,
        "solver_state_hash": solver_state_hash,
        "step_hash_step4": step_hash_step4,
        "step_hash_pass3": step_hash_pass3,
        "step_hash_p4": step_hash_p4,
        "pass12_phase": pass12_phase,
        "removed_counts": removed,
        "existing_layout_analysis": existing_layout_analysis,
        "before_return_validate": before_return_validate,
        "disconnected_stub_count": report.disconnected_stub_count,
        "quarantined_unrouted_count": report.quarantined_unrouted_count,
        "provisional_placed_row_count": report.provisional_placed_row_count,
        "missing_extractor_rotation_count": report.missing_extractor_rotation_count,
        "layout_degraded": layout_degraded,
        "geometry_valid": summary_geometry_valid,
        "connectivity_valid": report.connectivity_valid,
        "capacity_mode": "accumulate_only",
        "trunk_load": dict(step4_result.trunk_load),
        "routed_stub_count": int(step4_result.trunk_load.get("step4_routed_stub_count", 0)),
        "total_stub_count": int(step4_result.trunk_load.get("step4_total_stub_count", 0)),
        "route_cell_count": int(step4_result.trunk_load.get("step4_final_route_cell_count", 0)),
        "routing_failures": [dict(x) for x in step4_result.routing_failures],
        "routing_state": routing_state_summary,
        "step4_route_count": step4_result.trunk_load.get("step4_route_count", 0),
        "step4_routing_failure_count": step4_result.trunk_load.get(
            "step4_routing_failure_count", 0
        ),
        "step4_committed": step4_result.committed,
        "step4_skipped": bool(pass12_skipped),
        "placement_commit_counts": dict(step4_result.trunk_load.get("placement_commit_counts", {})),
        "rolled_back_placement_ids": list(step4_result.rolled_back_placement_ids),
        "step4_rolled_back_count": step4_rollback_count,
        "unfinalized_placement_count": unfinalized_placement_count,
        "route_revalidation_passed": step4_result.trunk_load.get("route_revalidation_passed", True),
        "broken_routed_route_count": step4_result.trunk_load.get("broken_routed_route_count", 0),
        "cascade_corrective_attempts": step4_result.trunk_load.get(
            "cascade_corrective_attempts", 0
        ),
        "cascade_reroute_count": step4_result.trunk_load.get("cascade_reroute_count", 0),
        "cascade_rollback_count": step4_result.trunk_load.get("cascade_rollback_count", 0),
        **pass12_trace_fields,
        **pass3_summary,
    }
    summary_fields["transport_connected"] = report.transport_connectivity_ok
    summary_fields["optimization_baseline_internal_transport"] = (
        optimization_baseline_internal_transport
    )
    summary_fields["optimization_baseline_internal_transport_post_step4"] = (
        optimization_baseline_internal_transport_post_step4
    )
    summary_fields["optimization_counterfactual_internal_transport_sequential_v1"] = (
        optimization_counterfactual_internal_transport_sequential_v1
    )
    summary_fields["optimization_counterfactual_failure_reason"] = (
        optimization_counterfactual_failure_reason
    )
    summary_fields["optimization_counterfactual_aggregation"] = (
        optimization_counterfactual_aggregation
    )
    _cf_it = optimization_counterfactual_internal_transport_sequential_v1
    _after_it = summary_fields.get("after_internal_transport_count")
    _quality_ratio: float | None = None
    if isinstance(_after_it, int) and isinstance(_cf_it, int) and _cf_it > 0:
        _quality_ratio = round(float(_after_it) / float(_cf_it), 6)
    summary_fields["optimization_internal_transport_quality_ratio"] = _quality_ratio
    enrich_solver_summary_recovery(
        summary_fields,
        report=report,
        step4_result=step4_result,
    )
    _append_optimization_warnings(summary_fields)
    if getattr(settings, "SHAPEZ_MINING_TRUNK_OBSERVATION_SOFT_CHECK", False):
        tw = trunk_load_observation_soft_warnings(map_final, step4_result.trunk_load)
        if tw:
            summary_fields["trunk_observation_soft_warnings"] = tw
    _replay_vals: dict[str, Any] = {
        "baseline_snapshot_kind": OPTIMIZATION_BASELINE_SNAPSHOT_PASS1_PASS2_PRE_STEP4,
        "baseline_internal_transport_count": optimization_baseline_internal_transport,
        "baseline_internal_transport_post_step4_count": (
            optimization_baseline_internal_transport_post_step4
        ),
        "final_internal_transport_count": summary_fields.get("after_internal_transport_count"),
        "optimization_warnings": list(summary_fields.get("optimization_warnings") or []),
        "counterfactual_internal_transport_sequential_v1": (
            optimization_counterfactual_internal_transport_sequential_v1
        ),
        "counterfactual_aggregation": optimization_counterfactual_aggregation,
        "counterfactual_failure_reason": optimization_counterfactual_failure_reason,
        "internal_transport_quality_ratio": _quality_ratio,
        "placement_candidate_blocked_count": _placement_candidate_blocked_count_from_pass12(
            pass12_stats
        ),
    }
    optimization_replay_metrics: dict[str, Any] = {
        k: _replay_vals[k] for k in OPTIMIZATION_REPLAY_METRIC_KEYS
    }
    solver_init_map = merge_with_transport_and_final_mining_map(
        map_timeline[0]["mining_map"],
        map_timeline[-1]["mining_map"],
    )
    frames: list[dict[str, Any]] = [
        {
            "id": SOLVER_FRAME_INIT,
            "summary": {"step": "init", **pass12_status_fields},
            "mining_map": solver_init_map,
        },
        {
            "id": SOLVER_FRAME_PASS1_OUTER,
            "summary": {
                "step": "pass1_outer_mvp",
                **pass12_status_fields,
                **_solver_stats_by_prefix(pass12_stats, "pass1_"),
            },
            "mining_map": map_after_pass1,
        },
        {
            "id": SOLVER_FRAME_PASS2_INTERNAL,
            "summary": {
                "step": "pass2_internal_mvp",
                **pass12_status_fields,
                **_solver_stats_by_prefix(pass12_stats, "pass2_"),
                "after_pass2_placement_counts": post_pass2_counts,
            },
            "mining_map": map_after_pass2,
        },
        {
            "id": SOLVER_FRAME_STEP4_ROUTING,
            "summary": {
                "step": "step4_merge_routing_mvp",
                **pass12_status_fields,
                "step4_committed": step4_result.committed,
                "step4_skipped": bool(pass12_skipped),
                "step4_route_count": step4_result.trunk_load.get("step4_route_count", 0),
                "step4_routing_failure_count": step4_result.trunk_load.get(
                    "step4_routing_failure_count", 0
                ),
                "step4_routed_count": step4_result.trunk_load.get("step4_routed_count", 0),
                "step4_rolled_back_count": step4_result.trunk_load.get(
                    "step4_rolled_back_count", 0
                ),
                "step4_quarantined_count": step4_result.trunk_load.get(
                    "step4_quarantined_count", 0
                ),
                "unfinalized_placement_count": unfinalized_placement_count,
                "route_revalidation_passed": step4_result.trunk_load.get(
                    "route_revalidation_passed", True
                ),
                "broken_routed_route_count": step4_result.trunk_load.get(
                    "broken_routed_route_count", 0
                ),
                "cascade_reroute_count": step4_result.trunk_load.get("cascade_reroute_count", 0),
                "cascade_rollback_count": step4_result.trunk_load.get("cascade_rollback_count", 0),
                "after_routing_counts": post_step4_counts,
                "routing_state": routing_state_summary,
                "trunk_load": dict(step4_result.trunk_load),
            },
            "mining_map": map_after_routing,
        },
        {
            "id": SOLVER_FRAME_PASS3_TRANSPORT,
            "summary": {
                "step": "pass3_transport_minimization",
                **pass12_status_fields,
                **pass3_summary,
            },
            "mining_map": map_final,
        },
        {
            "id": SOLVER_FRAME_VALIDATE,
            "summary": {
                **pass12_status_fields,
                "step": "final_validation",
                "geometry_valid": summary_geometry_valid,
                "connectivity_valid": report.connectivity_valid,
                "before_return_validate": before_return_validate,
                "recovery_context_chain": pass3_summary.get("recovery_context_chain", []),
                "recovery_trigger_reason": pass3_summary.get("recovery_trigger_reason"),
                "recovery_terminal_reason": pass3_summary.get("recovery_terminal_reason"),
            },
            "mining_map": map_final,
        },
    ]
    solver_replay = build_solver_replay_snapshot(
        frames=frames,
        run_id=run_id,
        events=replay_events,
        optimization_metrics=optimization_replay_metrics,
    )
    out = {
        "ok": return_reason == "ok",
        "return_reason": return_reason,
        "solver_timeline": frames,
        "solver_replay": solver_replay,
        "solver_summary": summary_fields,
        "existing_layout_analysis": existing_layout_analysis,
        "final_validation": {
            "geometry_valid": summary_geometry_valid,
            "connectivity_valid": report.connectivity_valid,
            "disconnected_stub_count": report.disconnected_stub_count,
            "orphan_transport_count": report.orphan_transport_count,
            "overlap_violation_count": report.overlap_violation_count,
            "missing_stub_count": report.missing_stub_count,
            "missing_extractor_rotation_count": report.missing_extractor_rotation_count,
            "quarantined_unrouted_count": report.quarantined_unrouted_count,
            "provisional_placed_row_count": report.provisional_placed_row_count,
            "unfinalized_placement_count": unfinalized_placement_count,
            "extractor_count": report.extractor_count,
            "extension_count": report.extension_count,
            "transport_cell_count": report.transport_cell_count,
            "transport_connectivity_ok": report.transport_connectivity_ok,
            "optimization_warnings": list(summary_fields.get("optimization_warnings") or []),
            "optimization_baseline_snapshot_kind": (
                OPTIMIZATION_BASELINE_SNAPSHOT_PASS1_PASS2_PRE_STEP4
            ),
            "optimization_baseline_internal_transport": optimization_baseline_internal_transport,
            "optimization_baseline_internal_transport_post_step4": (
                optimization_baseline_internal_transport_post_step4
            ),
            "optimization_final_internal_transport_count": summary_fields.get(
                "after_internal_transport_count"
            ),
            "optimization_counterfactual_internal_transport_sequential_v1": (
                optimization_counterfactual_internal_transport_sequential_v1
            ),
            "optimization_counterfactual_failure_reason": (
                optimization_counterfactual_failure_reason
            ),
            "optimization_counterfactual_aggregation": (optimization_counterfactual_aggregation),
            "optimization_internal_transport_quality_ratio": _quality_ratio,
        },
    }
    debug_log_event(
        debug_location,
        "pipeline_return",
        {
            "ok": out["ok"],
            "return_reason": return_reason,
            "timeline_frame_count": len(frames),
            "final_validation": out["final_validation"],
        },
    )
    return out, summary_fields


def apply_exception_summary_defaults(summary_fields: dict[str, Any]) -> None:
    """Exception path의 기존 solver_summary 기본값을 유지한다."""

    summary_fields.setdefault("geometry_valid", False)
    summary_fields.setdefault("connectivity_valid", False)
    summary_fields.setdefault("after_pass2_baseline_counts", {})
    summary_fields.setdefault("final_counts", {})
    summary_fields.setdefault("removed_counts", {})
    summary_fields.setdefault("disconnected_stub_count", 0)
    summary_fields.setdefault("quarantined_unrouted_count", 0)
    summary_fields.setdefault("provisional_placed_row_count", 0)
    summary_fields.setdefault("unfinalized_placement_count", 0)
    summary_fields.setdefault("missing_extractor_rotation_count", 0)
    summary_fields.setdefault("layout_degraded", True)
    summary_fields.setdefault("pass12_phase", "exception")
    summary_fields.setdefault("routing_state", None)
    summary_fields.setdefault("step4_route_count", 0)
    summary_fields.setdefault("step4_routing_failure_count", 0)
    summary_fields.setdefault("step4_committed", False)
    summary_fields.setdefault("step4_skipped", False)
    summary_fields.setdefault("pass12_mixed_surface_skipped", False)
    summary_fields.setdefault("placement_commit_counts", {})
    summary_fields.setdefault("rolled_back_placement_ids", [])
    summary_fields.setdefault("step4_rolled_back_count", 0)
    summary_fields.setdefault("route_revalidation_passed", True)
    summary_fields.setdefault("broken_routed_route_count", 0)
    summary_fields.setdefault("cascade_corrective_attempts", 0)
    summary_fields.setdefault("cascade_reroute_count", 0)
    summary_fields.setdefault("cascade_rollback_count", 0)
    summary_fields.setdefault("existing_layout_analysis", None)
    summary_fields.setdefault("existing_layout_source_kind", None)
    summary_fields.setdefault("existing_layout_hint_coord_count", 0)
    summary_fields.setdefault("existing_layout_barrier_cell_count", 0)
    summary_fields.setdefault("pass2_spine_seed_count", 0)
    summary_fields.setdefault("pass2_spine_priority_applied", False)
    summary_fields.setdefault("placement_candidate_blocked_count", 0)
    summary_fields.setdefault("before_return_validate", None)
    summary_fields.setdefault("step_hash_step4", None)
    summary_fields.setdefault("step_hash_pass3", None)
    summary_fields.setdefault("step_hash_p4", None)
    summary_fields.setdefault("solver_state_hash", None)
    summary_fields.setdefault("pass3_skipped", True)
    summary_fields.setdefault("pass3_skip_reason", None)
    summary_fields.setdefault("pass3_committed", False)
    summary_fields.setdefault("pass3_greedy_committed", None)
    summary_fields.setdefault("pass3_map_accepted", False)
    summary_fields.setdefault("pass3_attempted_commit", False)
    summary_fields.setdefault("pass3_final_committed", False)
    summary_fields.setdefault("pass3_gain", 0)
    summary_fields.setdefault("pass3_reverted", False)
    summary_fields.setdefault("pass3_rollback_reason", None)
    summary_fields.setdefault("before_pass3_counts", None)
    summary_fields.setdefault("after_pass3_counts", None)
    summary_fields.setdefault("pass3_transport_cells_removed", None)
    summary_fields.setdefault("pass3_transport_cells_removed_total", None)
    summary_fields.setdefault("before_internal_transport_count", None)
    summary_fields.setdefault("after_internal_transport_count", None)
    summary_fields.setdefault("before_transport_count", None)
    summary_fields.setdefault("after_transport_count", None)
    summary_fields.setdefault("pass3_internal_transport_saved", None)
    summary_fields.setdefault("pass3_commit_reason", None)
    summary_fields.setdefault("pass3_rejected_reason", None)
    summary_fields.setdefault("p4_reclaim_shadow_enabled", False)
    summary_fields.setdefault("p4_reclaim_shadow_skip_reason", "exception")
    summary_fields.setdefault("p4_reclaim_candidate_count", None)
    summary_fields.setdefault("p4_reclaim_accepted_shadow_count", None)
    summary_fields.setdefault("p4_reclaim_rejected_shadow_count", None)
    summary_fields.setdefault("p4_reclaim_internal_transport_budget", None)
    summary_fields.setdefault("p4_reclaim_internal_transport_projected_added", None)
    summary_fields.setdefault("p4_reclaim_best_candidate", None)
    summary_fields.setdefault("p4_reclaim_protected_corridor_source", None)
    summary_fields.setdefault("p4_reclaim_hard_protected_count", None)
    summary_fields.setdefault("p4_reclaim_soft_protected_count", None)
    summary_fields.setdefault("p4_reclaim_provisional_commit_attempted", False)
    summary_fields.setdefault("p4_reclaim_provisional_commit_committed", False)
    summary_fields.setdefault("p4_reclaim_provisional_commit_rollback_performed", False)
    summary_fields.setdefault("p4_reclaim_provisional_commit_rollback_reason", None)
    summary_fields.setdefault("p4_reclaim_selected_candidate", None)
    summary_fields.setdefault("p4_reclaim_selected_candidate_rank", None)
    summary_fields.setdefault("p4_reclaim_added_extractor_cells", [])
    summary_fields.setdefault("p4_reclaim_added_extension_cells", [])
    summary_fields.setdefault("p4_reclaim_added_stub_cells", [])
    summary_fields.setdefault("p4_reclaim_provisional_commit_skip_reason", None)
    summary_fields.setdefault("p4_reclaim_incremental_route_attempted", False)
    summary_fields.setdefault("p4_reclaim_incremental_route_committed", False)
    summary_fields.setdefault("p4_reclaim_incremental_route_rollback_performed", False)
    summary_fields.setdefault("p4_reclaim_incremental_route_rollback_reason", None)
    summary_fields.setdefault("p4_reclaim_incremental_route_skip_reason", None)
    summary_fields.setdefault("p4_reclaim_incremental_route_path_cells", None)
    summary_fields.setdefault("p4_reclaim_incremental_route_cells_added", [])
    summary_fields.setdefault(
        "p4_reclaim_incremental_route_b2_internal_transport_added",
        None,
    )
    summary_fields.setdefault("p4_reclaim_loop_max_iterations", None)
    summary_fields.setdefault("p4_reclaim_shadow_scan_limit", None)
    summary_fields.setdefault("p4_reclaim_final_route_cells_added", [])
    summary_fields.setdefault("p4_reclaim_soft_protected_candidate_cells_added", [])
    summary_fields.setdefault("p4_reclaim_route_zone_rebuilt", False)
    summary_fields.setdefault("p4_reclaim_mineable_excluded_by_route_cells", None)
    summary_fields.setdefault("p4_reclaim_route_zone_excluded_cumulative_count", 0)
    summary_fields.setdefault("p4_reclaim_last_commit_route_cells", [])
    summary_fields.setdefault("p4_reclaim_last_soft_protected_candidate_cells", [])
    summary_fields.setdefault("p4_reclaim_loop_iterations_executed", 0)
    summary_fields.setdefault("p4_reclaim_loop_successful_commits", 0)
    summary_fields.setdefault("p4_reclaim_loop_internal_transport_cumulative_added", 0)
    summary_fields.setdefault("p4_reclaim_loop_terminated_reason", None)
    summary_fields.setdefault("p4_soft_replace_attempted", False)
    summary_fields.setdefault("p4_soft_replace_committed", False)
    summary_fields.setdefault("p4_soft_replace_rejected_reason", None)
    summary_fields.setdefault("p4_soft_replace_old_cells", [])
    summary_fields.setdefault("p4_soft_replace_new_cells", [])
    summary_fields.setdefault("p4_soft_replace_connected", None)
    summary_fields.setdefault("p4_soft_replace_contract", None)
    summary_fields.setdefault("p4_soft_replace_attempt_count", 0)
    summary_fields.setdefault("p4_soft_replace_commit_count", 0)
    summary_fields.setdefault("p4_soft_replace_job_count", 0)
    summary_fields.setdefault("p4_soft_replace_jobs_attempted", 0)
    summary_fields.setdefault("p4_soft_replace_selected_job_index", None)
    summary_fields.setdefault("p4_soft_replace_rejected_reasons_by_job", [])
    summary_fields.setdefault("post_reclaim_pass3_reruns_used", 0)
    summary_fields.setdefault("post_reclaim_pass3_attempted", False)
    summary_fields.setdefault("post_reclaim_pass3_executed", False)
    summary_fields.setdefault("post_reclaim_pass3_skip_reason", None)
    summary_fields.setdefault("post_reclaim_pass3_map_accepted", None)
    summary_fields.setdefault("post_reclaim_pass3_pass3_reverted", False)
    summary_fields.setdefault("post_reclaim_pass3_ran", False)
    summary_fields.setdefault("baseline_internal_transport_at_reclaim_entry", None)
    summary_fields.setdefault("net_internal_transport_saved_after_reclaim", None)
    summary_fields.setdefault("post_reclaim_pass3_before_count", None)
    summary_fields.setdefault("post_reclaim_pass3_after_count", None)
    summary_fields.setdefault("post_reclaim_pass3_delta", None)
    summary_fields.setdefault("optimization_baseline_internal_transport", None)
    summary_fields.setdefault("optimization_baseline_internal_transport_post_step4", None)
    summary_fields.setdefault("optimization_counterfactual_internal_transport_sequential_v1", None)
    summary_fields.setdefault("optimization_counterfactual_failure_reason", None)
    summary_fields.setdefault("optimization_counterfactual_aggregation", None)
    summary_fields.setdefault("optimization_internal_transport_quality_ratio", None)
    summary_fields.setdefault("recovery_contract_phases", [])
    summary_fields.setdefault("recovery_total_attempts_used", 0)
    summary_fields.setdefault("validation_recovery_attempts_used", 0)
    summary_fields.setdefault("recovery_action_plan", [])
    summary_fields.setdefault("recovery_reclaim_incremental_failure", False)
    summary_fields.setdefault("recovery_merge_partial_failure", False)
    summary_fields.setdefault("recovery_post_reclaim_pass3_connectivity_break", False)
    summary_fields.setdefault("recovery_validation_recovery_eligible", False)
    summary_fields.setdefault("recovery_bounded_loop_configured", False)
    summary_fields.setdefault("max_total_recovery_attempts", MAX_TOTAL_RECOVERY_ATTEMPTS)
    summary_fields.setdefault(
        "max_validation_recovery_attempts", MAX_VALIDATION_RECOVERY_ATTEMPTS
    )
    summary_fields.setdefault("validation_recovery_cycles_used", 0)
    summary_fields.setdefault(
        "recovery_validation_outcome",
        {"commit_reason": None, "rollback_reason": None, "rejected_reason": None},
    )
    summary_fields.setdefault("optimization_warnings", [])
