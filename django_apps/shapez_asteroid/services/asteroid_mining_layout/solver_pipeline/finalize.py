"""Final validation, frame assembly, and summary contract helpers.

Algorithm §14 / §15: this module assembles STEP9 reports and summaries only. It must not create
or promote protected corridors (including ``ela_trunk_seed_candidate_corridors`` → hard), and
must not mutate the semantic ``routing_state`` dict passed in as ``routing_state_summary`` (same
object is echoed under ``solver_summary[\"routing_state\"]``).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django.conf import settings

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_TOTAL_RECOVERY_ATTEMPTS,
    MAX_VALIDATION_RECOVERY_ATTEMPTS,
    OPTIMIZATION_BASELINE_SNAPSHOT_PASS1_PASS2_PRE_STEP4,
    OPTIMIZATION_QUALITY_RATIO_WARN_THRESHOLD,
    OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE,
    OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_QUALITY_RATIO_HIGH,
    OPTIMIZATION_WARNING_PASS12_STUB_ROUTE_RECOVERY_DISABLED_WHILE_ELIGIBLE,
    SOLVER_FRAME_INIT,
    SOLVER_FRAME_PASS1_OUTER,
    SOLVER_FRAME_PASS2_INTERNAL,
    SOLVER_FRAME_PASS3_TRANSPORT,
    SOLVER_FRAME_STEP4_ROUTING,
    SOLVER_FRAME_VALIDATE,
    SOLVER_QUALITY_TIER_PARTIAL_SUCCESS_VALID_PRESERVE_LOSS,
    SOLVER_QUALITY_TIER_SOLVER_FAILURE,
    SOLVER_QUALITY_TIER_SUCCESS_VALID_OPTIMIZED,
    SOLVER_QUALITY_TIER_SUCCESS_VALID_WITH_OPTIMIZATION_WARNING,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (  # noqa: E501
    placement_state_counts,
    unfinalized_placement_count_from_placement_commit_by_id,
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
    replay_diag_counts_for_solver_summary,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.recovery_orchestrator import (  # noqa: E501
    enrich_solver_summary_recovery,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.step4_route_failure_solver_summary import (  # noqa: E501
    build_step4_route_failure_aggregate_for_solver_summary,
    empty_step4_route_failure_aggregate_for_solver_summary,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.validation_bridge import (  # noqa: E501
    validate_final_mining_layout_bridge as _validate_final_mining_layout,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_recovery_trigger as _s4_rt,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4RoutingResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_route_failure_replay_overlay import (  # noqa: E501
    merge_step4_route_failure_replay_overlay,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.trunk_load_observation_soft import (  # noqa: E501
    trunk_load_observation_soft_warnings,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import (
    merge_with_transport_and_final_mining_map,
)

SOLVER_TERMINATION_SUCCESS = "success"
SOLVER_TERMINATION_PARTIAL_SUCCESS = "partial_success"
SOLVER_TERMINATION_FAILURE = "solver_failure"

SOLVER_TERMINATION_TIER_SUCCESS = "SUCCESS"
SOLVER_TERMINATION_TIER_PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
SOLVER_TERMINATION_TIER_SOLVER_FAILURE = "SOLVER_FAILURE"

RETURN_REASON_STEP4_PARTIAL_FAILURE = "step4_partial_failure"

# ``solver_summary`` / ``final_validation`` — STEP4 returned layout lineage (API-stable literals).
STEP4_RETURNED_LAYOUT_SOURCE_FULL_STEP4_COMMIT = "full_step4_commit"
STEP4_RETURNED_LAYOUT_SOURCE_KNOWN_GOOD_AFTER_ROLLBACK = "known_good_after_rollback"
STEP4_RETURNED_LAYOUT_SOURCE_PRE_STEP4_BASELINE = "pre_step4_baseline"


def _solver_quality_summary_for_tier(tier: str) -> str:
    """Short English line for copy-preview / UI (not gettext; API-stable literal)."""

    if tier == SOLVER_QUALITY_TIER_SUCCESS_VALID_OPTIMIZED:
        return "Valid layout, fully optimized"
    if tier == SOLVER_QUALITY_TIER_SUCCESS_VALID_WITH_OPTIMIZATION_WARNING:
        return "Valid layout, optimization warning"
    if tier == SOLVER_QUALITY_TIER_PARTIAL_SUCCESS_VALID_PRESERVE_LOSS:
        return "Valid layout, preserve or routing degradation"
    if tier == SOLVER_QUALITY_TIER_SOLVER_FAILURE:
        return "Layout validation failed"
    return "Unknown solver quality tier"


def _compute_solver_quality_tier(
    *,
    layout_hard_valid: bool,
    solver_termination: str,
    optimization_warnings: list[str],
    extractor_drop_count: int,
) -> str:
    """Separate hard validity from optimization / preserve quality (reporting only).

    Precedence when hard-valid and termination is full success: extractor drop (vs merged seed)
    before optimization-only warnings, so ``PARTIAL_SUCCESS_VALID_PRESERVE_LOSS`` wins when both
    apply.
    """

    if not layout_hard_valid or solver_termination == SOLVER_TERMINATION_FAILURE:
        return SOLVER_QUALITY_TIER_SOLVER_FAILURE
    if solver_termination == SOLVER_TERMINATION_PARTIAL_SUCCESS:
        return SOLVER_QUALITY_TIER_PARTIAL_SUCCESS_VALID_PRESERVE_LOSS
    if extractor_drop_count > 0:
        return SOLVER_QUALITY_TIER_PARTIAL_SUCCESS_VALID_PRESERVE_LOSS
    if optimization_warnings:
        return SOLVER_QUALITY_TIER_SUCCESS_VALID_WITH_OPTIMIZATION_WARNING
    return SOLVER_QUALITY_TIER_SUCCESS_VALID_OPTIMIZED


# Bump when ``preserve_quality_score`` formula or inputs change (A/B / NDJSON comparability).
PRESERVE_QUALITY_SCORE_VERSION = 2


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


def _append_stub_route_recovery_disabled_warning(
    summary_fields: dict[str, Any],
) -> None:
    """After quality tier: flag eligible preserve miners when stub-route recovery was disabled."""

    elig = int(summary_fields.get("pass12_stub_route_recovery_eligible_count") or 0)
    if elig <= 0:
        return
    if bool(summary_fields.get("pass12_stub_route_recovery_enabled")):
        return
    ow = list(summary_fields.get("optimization_warnings") or [])
    code = OPTIMIZATION_WARNING_PASS12_STUB_ROUTE_RECOVERY_DISABLED_WHILE_ELIGIBLE
    if code not in ow:
        ow.append(code)
    summary_fields["optimization_warnings"] = ow
    summary_fields["optimization_warning_count"] = len(ow)


def _transport_cell_coords_from_map_rows(rows: list[dict[str, Any]]) -> frozenset[tuple[int, int]]:
    cells = cells_dict_from_mining_map(rows)
    return frozenset(c for c, r in cells.items() if r.get("role") in ("belt", "pipe"))


def _baseline_extension_count(mining_map: list[dict[str, Any]]) -> int:
    n = 0
    for row in mining_map:
        if row.get("role") != "occupied":
            continue
        layout_kind_value = layout_kind(row)
        if layout_kind_value in EXTENSIONS:
            n += 1
    return n


def preserve_quality_bundle_from_pass12(
    pass12_stats: Mapping[str, Any],
) -> tuple[dict[str, Any], float | None]:
    """Aggregate preserve-first seed metrics + scalar score for regression / dashboards."""

    orig = int(pass12_stats.get("pass12_merged_seed_miner_count") or 0)
    preserved = int(pass12_stats.get("pass12_preserved_bundle_extractor_cells") or 0)
    dropped = int(pass12_stats.get("pass12_preserved_missing_stub_drop_extractor_count") or 0)
    recovered_total = int(pass12_stats.get("pass12_preserved_recovery_success_count") or 0)
    rot_rec = int(pass12_stats.get("pass12_preserved_rotation_recovery_count") or 0)
    rr_att = int(
        pass12_stats.get("pass12_preserved_missing_stub_route_recovery_attempted_count") or 0
    )
    rr_ok = int(pass12_stats.get("pass12_preserved_missing_stub_route_recovery_success_count") or 0)
    stub_samples = pass12_stats.get("pass12_preserved_recovered_stub_samples")
    if not isinstance(stub_samples, list):
        stub_samples = []
    unrec_samples = pass12_stats.get("pass12_preserved_unrecovered_stub_drop_samples")
    if not isinstance(unrec_samples, list):
        unrec_samples = []
    bundle: dict[str, Any] = {
        "original_extractor_count": orig,
        "preserved_valid_count": preserved,
        "dropped_invalid_count": dropped,
        "recovered_stub_count": rr_ok,
        "recovered_rotation_count": rot_rec,
        "stub_route_recovery_attempted_count": rr_att,
        "stub_route_recovery_success_count": rr_ok,
        "recovered_stub_samples": stub_samples,
        "unrecovered_stub_drop_samples": unrec_samples,
        "preserve_quality_score_version": PRESERVE_QUALITY_SCORE_VERSION,
    }
    if orig <= 0:
        return bundle, None
    denominator = float(max(orig, 1))
    preserved_ratio = preserved / denominator
    dropped_ratio = dropped / denominator
    recovered_ratio = recovered_total / denominator
    score = preserved_ratio - dropped_ratio + 0.5 * recovered_ratio
    score_clamped = round(max(-1.0, min(1.0, score)), 6)
    return bundle, score_clamped


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


def _pass3_summary_for_solver_timeline(pass3_summary: Mapping[str, Any]) -> dict[str, Any]:
    """Strip ``pass3_commit_reason`` unless Pass3 finalized (STEP10 timeline summary contract)."""

    out = dict(pass3_summary)
    if not bool(out.get("pass3_final_committed")):
        out["pass3_commit_reason"] = None
    return out


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
    """최종 validation, summary, timeline, replay payload를 기존 schema로 조립한다.

    STEP4 semantics: ``step4_committed`` / ``Step4RoutingResult.committed`` is false whenever
    STEP4 did not achieve a full no-failure commit, but the returned ``map_final`` may still be
    **geometry/connectivity valid** with **zero unfinalized placements** after successful spatial
    rollback (``solver_termination=partial_success``, ``return_reason=step4_partial_failure``).
    In that case ``step4_returned_layout_source`` is ``known_good_after_rollback`` even though
    ``step4_committed`` remains false for backward compatibility.
    """

    report = _validate_final_mining_layout(map_final)
    post_routing_counts = count_layout_cells(map_final)
    layout_ok = report.geometry_valid and report.connectivity_valid
    map_fsm_unfinalized = int(report.provisional_placed_row_count) + int(
        report.quarantined_unrouted_count
    )
    placement_commit_fsm_unfinalized = unfinalized_placement_count_from_placement_commit_by_id(
        step4_result.placement_commit_by_id or {}
    )
    summary_unfinalized_placement_count = max(
        map_fsm_unfinalized,
        int(unfinalized_placement_count),
        placement_commit_fsm_unfinalized,
    )

    _layout_hard_valid = (
        bool(report.geometry_valid)
        and bool(report.connectivity_valid)
        and int(summary_unfinalized_placement_count) == 0
    )

    step4_routing_failure_count = int(
        step4_result.trunk_load.get("step4_routing_failure_count", 0) or 0
    )
    step4_partial_failure = (not pass12_skipped) and (
        (not step4_result.committed)
        or not step4_result.complete_routing_success
        or step4_routing_failure_count > 0
        or len(step4_result.rolled_back_placement_ids) > 0
        or len(step4_result.quarantined_placement_ids) > 0
    )

    # Termination tier is the authoritative contract; ok/return_reason are mapped from it.
    if (
        summary_unfinalized_placement_count > 0
        or not report.geometry_valid
        or not report.connectivity_valid
    ):
        solver_termination = SOLVER_TERMINATION_FAILURE
    elif step4_partial_failure:
        solver_termination = SOLVER_TERMINATION_PARTIAL_SUCCESS
    else:
        solver_termination = SOLVER_TERMINATION_SUCCESS

    if solver_termination == SOLVER_TERMINATION_PARTIAL_SUCCESS:
        assert (
            int(summary_unfinalized_placement_count) == 0
        ), "partial_success implies a finalized returned layout (no unfinalized placements)"

    if pass12_skipped:
        step4_returned_layout_source = STEP4_RETURNED_LAYOUT_SOURCE_PRE_STEP4_BASELINE
    elif not step4_partial_failure:
        step4_returned_layout_source = STEP4_RETURNED_LAYOUT_SOURCE_FULL_STEP4_COMMIT
    elif _layout_hard_valid:
        step4_returned_layout_source = STEP4_RETURNED_LAYOUT_SOURCE_KNOWN_GOOD_AFTER_ROLLBACK
    else:
        # Partial STEP4 without a hard-valid returned map (rare); not ``known_good_after_rollback``.
        step4_returned_layout_source = STEP4_RETURNED_LAYOUT_SOURCE_PRE_STEP4_BASELINE

    placement_pipeline_unfinalized = max(
        int(unfinalized_placement_count),
        placement_commit_fsm_unfinalized,
    )
    # Map FSM quarantine/provisional on merged cells are geometry failures; only STEP4 /
    # placement-commit unfinalized uses ``validation_unfinalized_placement_failed`` (bounded §11).

    if solver_termination == SOLVER_TERMINATION_PARTIAL_SUCCESS:
        return_reason = RETURN_REASON_STEP4_PARTIAL_FAILURE
    elif placement_pipeline_unfinalized > 0:
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

    after_pass2_extractor_count = int(post_pass2_counts.get("extractors", 0) or 0)
    post_step4_extractor_count = int(post_step4_counts.get("extractors", 0) or 0)
    step4_known_good_route_count = len(step4_result.routes)
    step4_failed_route_count = step4_routing_failure_count
    step4_rolled_back_placement_count = step4_rollback_count
    step4_quarantined_placement_count = len(step4_result.quarantined_placement_ids)
    internal_quarantined_count = int(
        step4_result.trunk_load.get("step4_quarantined_peak_count", 0)
        or step4_result.trunk_load.get("step4_quarantined_count", 0)
        or 0
    )
    step4_total_stub_count = int(step4_result.trunk_load.get("step4_total_stub_count", 0) or 0)
    if pass12_skipped:
        extractor_loss_due_to_step4_rollback = 0
        route_loss_due_to_step4_rollback = 0
    else:
        extractor_loss_due_to_step4_rollback = max(
            0, after_pass2_extractor_count - post_step4_extractor_count
        )
        route_loss_due_to_step4_rollback = max(
            0, step4_total_stub_count - step4_known_good_route_count
        )

    layout_degraded = (
        (not layout_ok)
        or unfinalized_placement_count > 0
        or step4_rollback_count > 0
        or broken_routed_n > 0
        or cascade_rb_n > 0
    )

    if solver_termination == SOLVER_TERMINATION_SUCCESS:
        termination_tier = SOLVER_TERMINATION_TIER_SUCCESS
    elif solver_termination == SOLVER_TERMINATION_PARTIAL_SUCCESS:
        termination_tier = SOLVER_TERMINATION_TIER_PARTIAL_SUCCESS
    else:
        termination_tier = SOLVER_TERMINATION_TIER_SOLVER_FAILURE

    degradation_causes: list[str] = []
    if solver_termination == SOLVER_TERMINATION_PARTIAL_SUCCESS:
        degradation_causes.append(return_reason)
    if layout_degraded and solver_termination != SOLVER_TERMINATION_FAILURE:
        degradation_causes.append("layout_degraded")
    summary_geometry_valid = report.geometry_valid and map_fsm_unfinalized == 0

    if getattr(settings, "SHAPEZ_MINING_ASSERT_STEP9_ROUTING_STATE", False):
        assert_protected_corridors_agree_with_transport_map(
            routing_state_summary,
            map_final,
            transport_kind=infer_transport_kind_from_mining_map(map_final),
            context="pre_return_step9",
        )

    # Read-only: counts and overlay derive from upstream STEP4/Reclaim routing_state only.
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
    _drop_n = int(
        pass12_trace_fields.get("pass12_preserved_missing_stub_drop_extractor_count") or 0
    )
    _rcounts = pass12_trace_fields.get("pass12_preserve_drop_reason_counts") or {}
    _ddetails = pass12_trace_fields.get("pass12_preserved_missing_stub_drop_details") or []
    _sample = _ddetails[:3] if isinstance(_ddetails, list) else []
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
            "orphan_shape_belt_count": report.orphan_shape_belt_count,
            "orphan_fluid_pipe_count": report.orphan_fluid_pipe_count,
            "fixed_output_stub_removed_count": report.fixed_output_stub_removed_count,
            "overlap_violation_count": report.overlap_violation_count,
            "missing_stub_count": report.missing_stub_count,
            "unfinalized_placement_count": summary_unfinalized_placement_count,
            "final_unfinalized_placement_count": int(summary_unfinalized_placement_count),
            "step4_partial_failure": bool(step4_partial_failure),
            "step4_returned_layout_source": step4_returned_layout_source,
            "internal_quarantined_count": int(internal_quarantined_count),
            "final_counts": post_routing_counts,
            "pass12_preserve_drop_trace": {
                "drop_count": _drop_n,
                "reason_counts": dict(_rcounts) if isinstance(_rcounts, dict) else {},
                "sample": _sample,
                "recovery_success_count": int(
                    pass12_trace_fields.get("pass12_preserved_recovery_success_count") or 0
                ),
            },
        },
    )
    removed = removed_counts_distribution(
        before_counts=pre_counts,
        after_counts=post_pass2_counts,
    )
    summary_fields = {
        "run_id": run_id,
        "return_reason": return_reason,
        "solver_termination": solver_termination,
        "termination": {
            "tier": termination_tier,
            "return_reason": return_reason,
            "degradation_causes": list(degradation_causes),
            "ok": solver_termination == SOLVER_TERMINATION_SUCCESS,
        },
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
        # Same dict reference as upstream STEP4 snapshot (Algorithm §14: no semantic mutation).
        "routing_state": routing_state_summary,
        "step4_route_count": step4_result.trunk_load.get("step4_route_count", 0),
        "step4_routing_failure_count": step4_result.trunk_load.get(
            "step4_routing_failure_count", 0
        ),
        "step4_complete_commit_success": bool(step4_result.committed),
        "step4_partial_failure": bool(step4_partial_failure),
        "step4_known_good_route_count": int(step4_known_good_route_count),
        "step4_failed_route_count": int(step4_failed_route_count),
        "step4_rolled_back_placement_count": int(step4_rolled_back_placement_count),
        "step4_quarantined_placement_count": int(step4_quarantined_placement_count),
        "step4_returned_layout_source": step4_returned_layout_source,
        "internal_quarantined_count": int(internal_quarantined_count),
        "final_unfinalized_placement_count": int(summary_unfinalized_placement_count),
        "after_pass2_extractor_count": int(after_pass2_extractor_count),
        "post_step4_extractor_count": int(post_step4_extractor_count),
        "extractor_loss_due_to_step4_rollback": int(extractor_loss_due_to_step4_rollback),
        "route_loss_due_to_step4_rollback": int(route_loss_due_to_step4_rollback),
        "step4_committed": step4_result.committed,
        "step4_complete_routing_success": bool(step4_result.complete_routing_success),
        "step4_skipped": bool(pass12_skipped),
        "placement_commit_counts": dict(step4_result.trunk_load.get("placement_commit_counts", {})),
        "rolled_back_placement_ids": list(step4_result.rolled_back_placement_ids),
        "step4_rolled_back_count": step4_rollback_count,
        "unfinalized_placement_count": summary_unfinalized_placement_count,
        "unfinalized_placement_count_map_fsm_rows": map_fsm_unfinalized,
        "unfinalized_placement_count_step4_trunk": unfinalized_placement_count,
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
    summary_fields.update(
        build_step4_route_failure_aggregate_for_solver_summary(step4_result.routing_failures)
    )
    summary_fields["step4_recovery_trigger"] = _s4_rt.step4_primary_recovery_trigger_from_result(
        step4_result
    )
    _rtr = summary_fields.get("recovery_trigger_reason")
    _rt = summary_fields.get("recovery_trigger")
    if _rt or _rtr:
        summary_fields["recovery_trigger_reason"] = str(_rtr or _rt)
    summary_fields["step4_no_route_exhausted_breakdown"] = summary_fields["trunk_load"].get(
        "step4_no_route_exhausted_breakdown"
    )
    summary_fields["step4_hard_protected_no_route_breakdown"] = summary_fields["trunk_load"].get(
        "step4_hard_protected_no_route_breakdown"
    )
    _pq, _pqs = preserve_quality_bundle_from_pass12(pass12_trace_fields)
    summary_fields["preserve_quality"] = _pq
    summary_fields["preserve_quality_score"] = _pqs
    summary_fields["preserve_quality_score_version"] = PRESERVE_QUALITY_SCORE_VERSION
    t_pass2 = _transport_cell_coords_from_map_rows(map_after_pass2)
    t_final = _transport_cell_coords_from_map_rows(map_final)
    summary_fields["existing_transport_reuse_ratio_final_vs_pass2"] = round(
        len(t_pass2 & t_final) / max(1, len(t_pass2)), 6
    )
    summary_fields["placement_state_counts"] = placement_state_counts(
        step4_result.placement_commit_by_id
    )
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
    _pq_b = summary_fields.get("preserve_quality")
    _orig_ext = (
        int((_pq_b or {}).get("original_extractor_count") or 0) if isinstance(_pq_b, dict) else 0
    )
    _final_ext = int(report.extractor_count)
    summary_fields["original_extractor_count"] = _orig_ext
    summary_fields["final_extractor_count"] = _final_ext
    summary_fields["extractor_drop_count"] = max(0, _orig_ext - _final_ext)
    _bl_it = summary_fields.get("optimization_baseline_internal_transport")
    _af_it = summary_fields.get("after_internal_transport_count")
    if isinstance(_bl_it, int) and isinstance(_af_it, int):
        summary_fields["internal_transport_delta_vs_baseline"] = int(_af_it) - int(_bl_it)
    else:
        summary_fields["internal_transport_delta_vs_baseline"] = None
    _ow_list = list(summary_fields.get("optimization_warnings") or [])
    summary_fields["optimization_warning_count"] = len(_ow_list)
    _qual_tier = _compute_solver_quality_tier(
        layout_hard_valid=_layout_hard_valid,
        solver_termination=solver_termination,
        optimization_warnings=_ow_list,
        extractor_drop_count=int(summary_fields["extractor_drop_count"]),
    )
    summary_fields["solver_quality_tier"] = _qual_tier
    summary_fields["solver_result_tier"] = _qual_tier
    summary_fields["solver_quality_summary"] = _solver_quality_summary_for_tier(_qual_tier)
    _append_stub_route_recovery_disabled_warning(summary_fields)
    _term_d = summary_fields.get("termination")
    if isinstance(_term_d, dict):
        _term_d["quality_tier"] = _qual_tier
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
                "step4_known_good_route_count": int(step4_known_good_route_count),
                "step4_failed_route_count": int(step4_failed_route_count),
                "step4_partial_failure": bool(step4_partial_failure),
                "internal_quarantined_count": int(internal_quarantined_count),
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
                **_pass3_summary_for_solver_timeline(pass3_summary),
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
                "final_unfinalized_placement_count": int(summary_unfinalized_placement_count),
                "step4_returned_layout_source": step4_returned_layout_source,
                "step4_partial_failure": bool(step4_partial_failure),
                "before_return_validate": before_return_validate,
                "recovery_context_chain": pass3_summary.get("recovery_context_chain", []),
                "recovery_trigger": pass3_summary.get("recovery_trigger"),
                "recovery_trigger_reason": pass3_summary.get("recovery_trigger_reason")
                or pass3_summary.get("recovery_trigger"),
                "p4_orchestration_entry_segment": pass3_summary.get(
                    "p4_orchestration_entry_segment"
                ),
                "recovery_terminal_reason": pass3_summary.get("recovery_terminal_reason"),
            },
            "mining_map": map_final,
        },
    ]
    summary_fields["solver_timeline_frame_count"] = len(frames)
    summary_fields["map_timeline_frame_count"] = len(map_timeline)
    summary_fields.update(replay_diag_counts_for_solver_summary())
    # ``replay_events`` is same-run append-only export for STEP10 / NDJSON — not a policy input
    # for routing or recovery (see ``solver_replay_events`` and ``solver_trace`` module docs).
    step4_fail_overlay = merge_step4_route_failure_replay_overlay(
        routing_failures=step4_result.routing_failures,
        routing_state=routing_state_summary,
        quarantined_placements=tuple(step4_result.quarantined_placement_ids_peak),
        rolled_back_placements=step4_result.rolled_back_placement_ids,
    )
    solver_replay = build_solver_replay_snapshot(
        frames=frames,
        run_id=run_id,
        events=replay_events,
        optimization_metrics=optimization_replay_metrics,
        existing_layout_analysis=existing_layout_analysis,
        placement_recovery_overlay={
            "step4_rolled_back_placement_ids": [
                str(x) for x in step4_result.rolled_back_placement_ids
            ],
            "step4_quarantined_placement_ids": [
                str(x) for x in step4_result.quarantined_placement_ids
            ],
            "step4_route_failure_replay_overlay": step4_fail_overlay,
        },
    )
    out = {
        # Backward-compatible: only full SUCCESS maps to ok=True.
        "ok": solver_termination == SOLVER_TERMINATION_SUCCESS,
        "return_reason": return_reason,
        "solver_termination": solver_termination,
        "termination": {
            "tier": termination_tier,
            "return_reason": return_reason,
            "degradation_causes": list(degradation_causes),
            "ok": solver_termination == SOLVER_TERMINATION_SUCCESS,
        },
        "solver_timeline": frames,
        "solver_replay": solver_replay,
        "solver_summary": summary_fields,
        "existing_layout_analysis": existing_layout_analysis,
        "final_validation": {
            "geometry_valid": summary_geometry_valid,
            "connectivity_valid": report.connectivity_valid,
            "disconnected_stub_count": report.disconnected_stub_count,
            "orphan_transport_count": report.orphan_transport_count,
            "orphan_shape_belt_count": report.orphan_shape_belt_count,
            "orphan_fluid_pipe_count": report.orphan_fluid_pipe_count,
            "fixed_output_stub_removed_count": report.fixed_output_stub_removed_count,
            "overlap_violation_count": report.overlap_violation_count,
            "missing_stub_count": report.missing_stub_count,
            "missing_extractor_rotation_count": report.missing_extractor_rotation_count,
            "quarantined_unrouted_count": report.quarantined_unrouted_count,
            "provisional_placed_row_count": report.provisional_placed_row_count,
            "unfinalized_placement_count": summary_unfinalized_placement_count,
            "final_unfinalized_placement_count": int(summary_unfinalized_placement_count),
            "step4_partial_failure": bool(step4_partial_failure),
            "step4_returned_layout_source": step4_returned_layout_source,
            "internal_quarantined_count": int(internal_quarantined_count),
            "after_pass2_extractor_count": int(after_pass2_extractor_count),
            "extractor_loss_due_to_step4_rollback": int(extractor_loss_due_to_step4_rollback),
            "route_loss_due_to_step4_rollback": int(route_loss_due_to_step4_rollback),
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
            "original_extractor_count": summary_fields.get("original_extractor_count"),
            "final_extractor_count": summary_fields.get("final_extractor_count"),
            "extractor_drop_count": summary_fields.get("extractor_drop_count"),
            "optimization_warning_count": summary_fields.get("optimization_warning_count"),
            "internal_transport_delta_vs_baseline": summary_fields.get(
                "internal_transport_delta_vs_baseline"
            ),
            "solver_quality_tier": summary_fields.get("solver_quality_tier"),
            "solver_result_tier": summary_fields.get("solver_result_tier"),
            "solver_quality_summary": summary_fields.get("solver_quality_summary"),
        },
    }
    _term_out = out.get("termination")
    if isinstance(_term_out, dict):
        _term_out["quality_tier"] = summary_fields.get("solver_quality_tier")
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
    """Exception path용 solver_summary 기본값.

    ``solver_service._initial_summary_fields``가 이미 채우는 키(``existing_layout_analysis``,
    ``before_return_validate``, ``step_hash_*``, ``solver_state_hash``)는 여기서 중복
    ``setdefault`` 하지 않는다.
    """

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
    summary_fields.setdefault("solver_termination", SOLVER_TERMINATION_FAILURE)
    summary_fields.setdefault(
        "termination",
        {
            "tier": SOLVER_TERMINATION_TIER_SOLVER_FAILURE,
            "return_reason": str(summary_fields.get("return_reason") or "exception"),
            "degradation_causes": ["exception"],
            "ok": False,
        },
    )
    summary_fields.setdefault("routing_state", None)
    summary_fields.setdefault("step4_route_count", 0)
    summary_fields.setdefault("step4_routing_failure_count", 0)
    summary_fields.setdefault("step4_no_route_exhausted_breakdown", None)
    summary_fields.setdefault("step4_hard_protected_no_route_breakdown", None)
    summary_fields.setdefault("step4_complete_commit_success", False)
    summary_fields.setdefault("step4_partial_failure", True)
    summary_fields.setdefault("step4_known_good_route_count", 0)
    summary_fields.setdefault("step4_failed_route_count", 0)
    summary_fields.setdefault("step4_rolled_back_placement_count", 0)
    summary_fields.setdefault("step4_quarantined_placement_count", 0)
    summary_fields.setdefault(
        "step4_returned_layout_source", STEP4_RETURNED_LAYOUT_SOURCE_PRE_STEP4_BASELINE
    )
    summary_fields.setdefault("internal_quarantined_count", 0)
    summary_fields.setdefault("final_unfinalized_placement_count", 0)
    summary_fields.setdefault("after_pass2_extractor_count", 0)
    summary_fields.setdefault("post_step4_extractor_count", 0)
    summary_fields.setdefault("extractor_loss_due_to_step4_rollback", 0)
    summary_fields.setdefault("route_loss_due_to_step4_rollback", 0)
    summary_fields.setdefault("step4_committed", False)
    summary_fields.setdefault("step4_skipped", False)
    summary_fields.setdefault("pass12_mixed_surface_skipped", False)
    summary_fields.setdefault("pass12_preserve_drop_reason_counts", {})
    summary_fields.setdefault("preserve_quality", {})
    summary_fields.setdefault("preserve_quality_score", None)
    summary_fields.setdefault("preserve_quality_score_version", PRESERVE_QUALITY_SCORE_VERSION)
    summary_fields.setdefault("placement_commit_counts", {})
    summary_fields.setdefault("rolled_back_placement_ids", [])
    summary_fields.setdefault("step4_rolled_back_count", 0)
    summary_fields.setdefault("route_revalidation_passed", True)
    summary_fields.setdefault("broken_routed_route_count", 0)
    summary_fields.setdefault("cascade_corrective_attempts", 0)
    summary_fields.setdefault("cascade_reroute_count", 0)
    summary_fields.setdefault("cascade_rollback_count", 0)
    summary_fields.setdefault("existing_layout_source_kind", None)
    summary_fields.setdefault("existing_layout_hint_coord_count", 0)
    summary_fields.setdefault("existing_layout_barrier_cell_count", 0)
    summary_fields.setdefault("pass2_spine_seed_count", 0)
    summary_fields.setdefault("pass2_spine_priority_applied", False)
    summary_fields.setdefault("placement_candidate_blocked_count", 0)
    summary_fields.setdefault("pass3_skipped", True)
    summary_fields.setdefault("pass3_skip_reason", None)
    summary_fields.setdefault("pass3_committed", False)
    summary_fields.setdefault("pass3_greedy_committed", None)
    summary_fields.setdefault("pass3_greedy_local_replacement", None)
    summary_fields.setdefault("pass3_map_accepted", False)
    summary_fields.setdefault("pass3_validated_layout_retained", False)
    summary_fields.setdefault("pass3_transport_stage_committed", False)
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
    summary_fields.setdefault("pass3_reclaim_projected_net_internal_saved", None)
    summary_fields.setdefault("pass3_commit_reason", None)
    summary_fields.setdefault("pass3_commit_subtype", None)
    summary_fields.setdefault("p4_orchestration_entry_segment", None)
    summary_fields.setdefault("recovery_trigger", None)
    summary_fields.setdefault("recovery_trigger_reason", None)
    summary_fields.setdefault("step4_recovery_trigger", None)
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
    summary_fields.setdefault("provisional_net_internal_transport_saved_after_reclaim", None)
    summary_fields.setdefault("p4_reclaim_provisional_reject_count", 0)
    summary_fields.setdefault("p4_reclaim_provisional_last_reject_reason", None)
    summary_fields.setdefault("p4_reclaim_soft_active_on_map_count", None)
    summary_fields.setdefault("p4_reclaim_zero_candidate_reasons", None)
    summary_fields.setdefault("mineable_base_count", None)
    summary_fields.setdefault("excluded_by_final_route_count", None)
    summary_fields.setdefault("excluded_by_hard_protected_count", None)
    summary_fields.setdefault("excluded_by_soft_protected_count", None)
    summary_fields.setdefault("excluded_by_committed_placement_count", None)
    summary_fields.setdefault("mineable_cur_count", None)
    summary_fields.setdefault("p4_reclaim_transport_total", None)
    summary_fields.setdefault("p4_reclaim_unprotected_transport_count", None)
    summary_fields.setdefault("p4_reclaim_final_route_count", None)
    summary_fields.setdefault("p4_soft_replace_attempted", False)
    summary_fields.setdefault("p4_soft_replace_committed", False)
    summary_fields.setdefault("p4_soft_replace_rejected_reason", None)
    summary_fields.setdefault("p4_soft_replace_connected", None)
    summary_fields.setdefault("p4_soft_replace_contract", None)
    summary_fields.setdefault("p4_soft_replace_attempt_count", 0)
    summary_fields.setdefault("p4_soft_replace_commit_count", 0)
    summary_fields.setdefault("p4_soft_replace_job_count", 0)
    summary_fields.setdefault("p4_soft_replace_jobs_attempted", 0)
    summary_fields.setdefault("p4_soft_replace_rejected_reasons_by_job", [])
    summary_fields.setdefault("post_reclaim_pass3_greedy_local_replacement", None)
    summary_fields.setdefault("post_reclaim_pass3_pass3_greedy_local_replacement", None)
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
    summary_fields.setdefault("max_recovery_context_chain_segments", None)
    summary_fields.setdefault("recovery_context_chain_segment_count", 0)
    summary_fields.setdefault("max_validation_recovery_attempts", MAX_VALIDATION_RECOVERY_ATTEMPTS)
    summary_fields.setdefault("validation_recovery_cycles_used", 0)
    summary_fields.setdefault(
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
    summary_fields.setdefault("optimization_warnings", [])
    summary_fields.setdefault("original_extractor_count", 0)
    summary_fields.setdefault("final_extractor_count", 0)
    summary_fields.setdefault("extractor_drop_count", 0)
    summary_fields.setdefault("optimization_warning_count", 0)
    summary_fields.setdefault("internal_transport_delta_vs_baseline", None)
    summary_fields.setdefault("solver_quality_tier", SOLVER_QUALITY_TIER_SOLVER_FAILURE)
    summary_fields.setdefault("solver_result_tier", SOLVER_QUALITY_TIER_SOLVER_FAILURE)
    summary_fields.setdefault(
        "solver_quality_summary",
        _solver_quality_summary_for_tier(SOLVER_QUALITY_TIER_SOLVER_FAILURE),
    )
    _term_exc = summary_fields.get("termination")
    if isinstance(_term_exc, dict):
        _term_exc.setdefault("quality_tier", summary_fields.get("solver_quality_tier"))
    _t5_empty = empty_step4_route_failure_aggregate_for_solver_summary()
    for _k, _v in _t5_empty.items():
        summary_fields.setdefault(_k, _v)
    summary_fields.setdefault("step4_complete_routing_success", False)
