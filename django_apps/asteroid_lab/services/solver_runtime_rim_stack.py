"""Run L3 rim greedy placement after L2 (Lab solver runtime)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from django_apps.asteroid_lab.layers.contracts.candidates import (
    Layer03SkipReason,
    RimBundleCandidateSet,
)
from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_03_RIM_MINING_BUNDLES,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
)
from django_apps.asteroid_lab.layers.contracts.rim_greedy import IntegratedRimGreedyResult
from django_apps.asteroid_lab.layers.contracts.rim_placement import Layer04RimPlacementResult
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from django_apps.asteroid_lab.layers.stack_runner import LAYER_STACK_BUDGET_MS
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap

_LEGACY_RIM_SLUGS = (LAYER_03_RIM_MINING_BUNDLES, LAYER_04_RIM_BUNDLE_PLACEMENT)


def _merge_legacy_candidate_set(
    solver_summary: dict[str, Any],
    *,
    layer03: RimBundleCandidateSet,
    layer04: Layer04RimPlacementResult,
) -> None:
    metrics = layer03.metrics
    solver_summary["rim_anchor_count"] = metrics.rim_anchor_count
    solver_summary["normal_candidate_count"] = metrics.normal_candidate_count
    solver_summary["route_probe_attempt_count"] = metrics.route_probe_attempt_count
    solver_summary["route_probe_succeeded_count"] = metrics.route_probe_succeeded_count
    solver_summary["route_probe_failed_count"] = metrics.route_probe_failed_count
    solver_summary["seed_projection_attempt_count"] = metrics.seed_projection_attempt_count
    solver_summary["local_geometry_rejected_count"] = metrics.local_geometry_rejected_count
    solver_summary["exterior_direction_candidate_count"] = (
        metrics.exterior_direction_candidate_count
    )
    solver_summary["direction_seed_attempt_count"] = metrics.direction_seed_attempt_count
    solver_summary["mining_footprint_prefilter_rejected_count"] = (
        metrics.mining_footprint_prefilter_rejected_count
    )
    solver_summary["field_route_cell_count_total"] = metrics.field_route_cell_count_total
    solver_summary["weighted_route_cost_total"] = metrics.weighted_route_cost_total
    solver_summary["transport_blocked_by_mining_count"] = metrics.transport_blocked_by_mining_count
    solver_summary["layer03_skip_reason"] = metrics.layer_skip_reason.value
    solver_summary["layer03_reject_reason_counts"] = list(metrics.reject_reason_counts)
    solver_summary["layer04_selected_count"] = layer04.selected_count
    solver_summary["layer04_rejected_overlap_count"] = layer04.rejected_overlap_count
    solver_summary["layer04_rejected_budget_count"] = layer04.rejected_budget_count
    solver_summary["overlay_occupied_cell_count"] = len(layer04.provisional_overlay.occupied_cells)

    completed = list(solver_summary.get("completed_layer_slugs") or [])
    rim_layers_ran = metrics.layer_skip_reason is Layer03SkipReason.NONE
    if rim_layers_ran:
        for slug in _LEGACY_RIM_SLUGS:
            if slug not in completed:
                completed.append(slug)
    else:
        completed = [slug for slug in completed if slug not in _LEGACY_RIM_SLUGS]
    solver_summary["completed_layer_slugs"] = completed

    steps = list(solver_summary.get("algorithm_steps") or [])
    for step in ("layer_03_rim_mining_bundles", "layer_04_rim_bundle_placement"):
        if step not in steps:
            steps.append(step)
    solver_summary["algorithm_steps"] = steps


def _merge_integrated_greedy(
    solver_summary: dict[str, Any],
    *,
    rim_greedy: IntegratedRimGreedyResult,
) -> None:
    metrics = rim_greedy.metrics
    solver_summary["rim_anchor_count"] = metrics.rim_anchor_count
    solver_summary["normal_candidate_count"] = metrics.committed_placement_count
    solver_summary["route_probe_attempt_count"] = (
        metrics.committed_placement_count + metrics.rejected_attempt_count
    )
    solver_summary["route_probe_succeeded_count"] = metrics.committed_placement_count
    solver_summary["route_probe_failed_count"] = metrics.rejected_attempt_count
    solver_summary["seed_projection_attempt_count"] = 0
    solver_summary["local_geometry_rejected_count"] = 0
    solver_summary["exterior_direction_candidate_count"] = 0
    solver_summary["direction_seed_attempt_count"] = 0
    solver_summary["mining_footprint_prefilter_rejected_count"] = 0
    solver_summary["field_route_cell_count_total"] = metrics.reserved_route_cell_count
    solver_summary["transport_blocked_by_mining_count"] = 0
    solver_summary["layer03_skip_reason"] = metrics.layer_skip_reason or "none"
    reject_counts = Counter(r.reason.value for r in rim_greedy.rejected_attempts)
    solver_summary["layer03_reject_reason_counts"] = sorted(
        reject_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )
    solver_summary["rim_greedy_winning_variant_id"] = metrics.winning_variant_id
    solver_summary["rim_greedy_pass2_score"] = metrics.pass2_score
    solver_summary["rim_greedy_total_route_length"] = rim_greedy.pass2_report.total_route_length
    solver_summary["rim_greedy_committed_count"] = metrics.committed_placement_count
    solver_summary["rim_greedy_rejected_count"] = metrics.rejected_attempt_count
    solver_summary["weighted_route_cost_total"] = rim_greedy.pass2_report.total_route_length
    solver_summary["layer04_selected_count"] = metrics.committed_placement_count
    solver_summary["layer04_rejected_overlap_count"] = 0
    solver_summary["layer04_rejected_budget_count"] = 0
    append = rim_greedy.append_result
    solver_summary["layer03_append_placement_count"] = append.placement_count
    solver_summary["layer03_append_cell_count"] = len(append.cells)
    solver_summary["layer03_append_route_reserved_count"] = append.route_reserved_cell_count
    solver_summary["overlay_occupied_cell_count"] = len(
        rim_greedy.provisional_overlay.occupied_cells
    )

    completed = list(solver_summary.get("completed_layer_slugs") or [])
    rim_layers_ran = metrics.layer_skip_reason is None
    if rim_layers_ran:
        if LAYER_03_RIM_GREEDY_PLACEMENT not in completed:
            completed.append(LAYER_03_RIM_GREEDY_PLACEMENT)
        completed = [slug for slug in completed if slug not in _LEGACY_RIM_SLUGS]
    else:
        excluded = (*_LEGACY_RIM_SLUGS, LAYER_03_RIM_GREEDY_PLACEMENT)
        completed = [slug for slug in completed if slug not in excluded]
    solver_summary["completed_layer_slugs"] = completed

    steps = list(solver_summary.get("algorithm_steps") or [])
    if "layer_03_rim_greedy_placement" not in steps:
        steps.append("layer_03_rim_greedy_placement")
    solver_summary["algorithm_steps"] = steps


def merge_rim_stack_into_solver_summary(
    solver_summary: dict[str, Any],
    *,
    layer03: RimBundleCandidateSet | IntegratedRimGreedyResult,
    layer04: Layer04RimPlacementResult | None = None,
) -> None:
    """Attach L3 rim metrics for Lab UI layer summaries (output-only)."""
    if isinstance(layer03, IntegratedRimGreedyResult):
        _merge_integrated_greedy(solver_summary, rim_greedy=layer03)
        return
    if layer04 is None:
        msg = "layer04 required when layer03 is RimBundleCandidateSet"
        raise TypeError(msg)
    _merge_legacy_candidate_set(solver_summary, layer03=layer03, layer04=layer04)


def run_rim_stack_layers_03_and_04(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext | None = None,
) -> IntegratedRimGreedyResult:
    ctx = budget_ctx or LayerBudgetContext.from_budget_ms(LAYER_STACK_BUDGET_MS)
    return run_layer_03_rim_greedy_placement(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        budget_ctx=ctx,
    )


__all__ = [
    "merge_rim_stack_into_solver_summary",
    "run_rim_stack_layers_03_and_04",
]
