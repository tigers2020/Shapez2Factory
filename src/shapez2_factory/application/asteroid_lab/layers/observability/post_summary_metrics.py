"""Pure per-layer post-summary metric builders (Django-free core)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    RimBundleCandidateSet,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)
from shapez2_factory.application.asteroid_lab.layers.layer_01_reconstruction.output import (
    Layer01ReconstructionOutput,
)


def build_layer01_post_summary_metrics(
    layer01: Layer01ReconstructionOutput,
) -> dict[str, object]:
    complete = layer01.complete_map
    return {
        "complete_map_cell_count": len(complete.cells),
        "shape_field_cell_count": int(complete.shape_field_cell_count),
        "fluid_field_cell_count": int(complete.fluid_field_cell_count),
        "external_void_cell_count": len(complete.external_void_cells),
        "coord_frame": str(complete.coord_frame.value),
    }


def build_layer02_post_summary_metrics(plan: ExteriorConnectionPlan) -> dict[str, object]:
    required_planned = sum(
        1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.REQUIRED
    )
    spare_planned = len(plan.planned_connectors) - required_planned
    return {
        "transport_kind": plan.transport_kind,
        "terrain_upper_bound_per_min": str(plan.terrain_upper_bound_per_min),
        "planning_target_per_min": str(plan.planning_target_per_min),
        "required_connector_count": plan.required_connector_count,
        "reference_connector_count": plan.reference_connector_count,
        "spare_connector_count": plan.spare_connector_count,
        "planned_connector_count": len(plan.planned_connectors),
        "required_planned_count": required_planned,
        "spare_planned_count": spare_planned,
        "unmet_reason": plan.unmet_reason.value if plan.unmet_reason is not None else None,
    }


def build_layer03_rim_greedy_post_summary_metrics(
    result: IntegratedRimGreedyResult,
) -> dict[str, object]:
    metrics = result.metrics
    append = result.append_result
    return {
        "rim_anchor_count": metrics.rim_anchor_count,
        "committed_placement_count": metrics.committed_placement_count,
        "rejected_attempt_count": metrics.rejected_attempt_count,
        "reserved_route_cell_count": metrics.reserved_route_cell_count,
        "winning_variant_id": metrics.winning_variant_id,
        "pass2_score": metrics.pass2_score,
        "layer_skip_reason": metrics.layer_skip_reason,
        "canonical_layer_slug": metrics.canonical_layer_slug,
        "append_placement_count": append.placement_count,
        "append_cell_count": len(append.cells),
        "append_route_reserved_cell_count": append.route_reserved_cell_count,
    }


def build_layer03_post_summary_metrics(result: RimBundleCandidateSet) -> dict[str, object]:
    metrics = result.metrics
    return {
        "rim_anchor_count": metrics.rim_anchor_count,
        "seed_projection_attempt_count": metrics.seed_projection_attempt_count,
        "exterior_direction_candidate_count": metrics.exterior_direction_candidate_count,
        "direction_seed_attempt_count": metrics.direction_seed_attempt_count,
        "mining_footprint_prefilter_rejected_count": (
            metrics.mining_footprint_prefilter_rejected_count
        ),
        "local_geometry_rejected_count": metrics.local_geometry_rejected_count,
        "route_probe_attempt_count": metrics.route_probe_attempt_count,
        "route_probe_succeeded_count": metrics.route_probe_succeeded_count,
        "route_probe_failed_count": metrics.route_probe_failed_count,
        "dedupe_duplicate_count": metrics.dedupe_duplicate_count,
        "normal_candidate_count": metrics.normal_candidate_count,
        "diagnostic_rejected_count": metrics.diagnostic_rejected_count,
        "budget_skipped_count": metrics.budget_skipped_count,
        "layer_skip_reason": metrics.layer_skip_reason.value,
        "reject_reason_counts": list(metrics.reject_reason_counts),
        "field_route_cell_count_total": metrics.field_route_cell_count_total,
        "weighted_route_cost_total": metrics.weighted_route_cost_total,
        "transport_blocked_by_mining_count": metrics.transport_blocked_by_mining_count,
    }


def build_layer05_post_summary_metrics() -> dict[str, object]:
    return {"stub": True}


def build_layer06_post_summary_metrics() -> dict[str, object]:
    return {"stub": True}


__all__ = [
    "build_layer01_post_summary_metrics",
    "build_layer02_post_summary_metrics",
    "build_layer03_post_summary_metrics",
    "build_layer03_rim_greedy_post_summary_metrics",
    "build_layer05_post_summary_metrics",
    "build_layer06_post_summary_metrics",
]
