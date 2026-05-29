"""Run L3 rim expansion + L4 provisional placement after L2 (Lab solver runtime)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.layers.contracts.candidates import (
    Layer03SkipReason,
    RimBundleCandidateSet,
)
from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_MINING_BUNDLES,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
)
from django_apps.asteroid_lab.layers.contracts.rim_placement import Layer04RimPlacementResult
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.run import (
    run_layer_03_rim_mining_bundles,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
    run_layer_04_rim_bundle_placement,
)
from django_apps.asteroid_lab.layers.stack_runner import LAYER_STACK_BUDGET_MS
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap


def merge_rim_stack_into_solver_summary(
    solver_summary: dict[str, Any],
    *,
    layer03: RimBundleCandidateSet,
    layer04: Layer04RimPlacementResult,
) -> None:
    """Attach L3/L4 metrics for Lab UI layer summaries (output-only)."""

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
        for slug in (LAYER_03_RIM_MINING_BUNDLES, LAYER_04_RIM_BUNDLE_PLACEMENT):
            if slug not in completed:
                completed.append(slug)
    else:
        completed = [
            slug
            for slug in completed
            if slug
            not in (
                LAYER_03_RIM_MINING_BUNDLES,
                LAYER_04_RIM_BUNDLE_PLACEMENT,
            )
        ]
    solver_summary["completed_layer_slugs"] = completed

    steps = list(solver_summary.get("algorithm_steps") or [])
    for step in ("layer_03_rim_mining_bundles", "layer_04_rim_bundle_placement"):
        if step not in steps:
            steps.append(step)
    solver_summary["algorithm_steps"] = steps


def run_rim_stack_layers_03_and_04(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext | None = None,
) -> tuple[RimBundleCandidateSet, Layer04RimPlacementResult]:
    ctx = budget_ctx or LayerBudgetContext.from_budget_ms(LAYER_STACK_BUDGET_MS)
    layer03 = run_layer_03_rim_mining_bundles(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        budget_ctx=ctx,
    )
    layer04 = run_layer_04_rim_bundle_placement(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        candidate_set=layer03,
        budget_ctx=ctx,
    )
    return layer03, layer04


__all__ = [
    "merge_rim_stack_into_solver_summary",
    "run_rim_stack_layers_03_and_04",
]
