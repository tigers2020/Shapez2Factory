"""Per-layer behavior patterns and one-line summary formatters (observability only)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer_post_summary import LayerPostSummaryOutcome
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_01_RECONSTRUCTION,
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_MINING_BUNDLES,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
    LAYER_05_INNER_PATTERN_FILL,
    LAYER_06_COMMIT_VALIDATE,
)

LAYER_BEHAVIOR_BY_SLUG: dict[str, str] = {
    LAYER_01_RECONSTRUCTION: (
        "Deconstruct snapshot → topology reconstruction → ReconstructionCompleteMap "
        "(field cells, external void, capacity envelope)."
    ),
    LAYER_02_EXTERIOR_TRANSPORT: (
        "Plan required and spare exterior connectors on void rim slots; "
        "emit belt/pipe stubs toward the shape field at terrain throughput target."
    ),
    LAYER_03_RIM_MINING_BUNDLES: (
        "Enumerate outer-rim anchors; project miner seeds; immediate route probe; "
        "dedupe by equivalence key into the normal candidate pool (overlap allowed)."
    ),
    LAYER_04_RIM_BUNDLE_PLACEMENT: (
        "Deterministic non-overlap selection from route-probed pool; "
        "emit PROVISIONAL_PLACED cells and ProvisionalLayoutOverlay (no commit)."
    ),
    LAYER_05_INNER_PATTERN_FILL: (
        "Fill interior pattern from complete_map + provisional overlay "
        "(stub in PR-3c; no committed layout mutation)."
    ),
    LAYER_06_COMMIT_VALIDATE: (
        "Re-probe route domain and commit ROUTED_CONFIRMED placements; "
        "structural validation gate (stub in PR-3c)."
    ),
}


def layer_behavior_for_slug(layer_slug: str) -> str:
    return LAYER_BEHAVIOR_BY_SLUG.get(
        layer_slug,
        "Layer stack step (behavior catalog entry not defined).",
    )


def format_layer_summary_line(
    layer_slug: str,
    *,
    outcome: LayerPostSummaryOutcome,
    metrics: dict[str, object],
) -> str:
    if outcome is LayerPostSummaryOutcome.SKIPPED_BUDGET:
        reason = metrics.get("reason", "budget_exhausted")
        return f"skipped_budget: {reason}"

    if layer_slug == LAYER_01_RECONSTRUCTION:
        return (
            f"shape_field={metrics.get('shape_field_cell_count')} "
            f"fluid_field={metrics.get('fluid_field_cell_count')} "
            f"void={metrics.get('external_void_cell_count')}"
        )
    if layer_slug == LAYER_02_EXTERIOR_TRANSPORT:
        unmet = metrics.get("unmet_reason")
        return (
            f"planned={metrics.get('planned_connector_count')} "
            f"required={metrics.get('required_connector_count')} "
            f"spare={metrics.get('spare_connector_count')} "
            f"unmet={unmet or 'none'}"
        )
    if layer_slug == LAYER_03_RIM_MINING_BUNDLES:
        return (
            f"rim_anchors={metrics.get('rim_anchor_count')} "
            f"pool={metrics.get('normal_candidate_count')} "
            f"probe_ok={metrics.get('route_probe_succeeded_count')}/"
            f"{metrics.get('route_probe_attempt_count')} "
            f"skip={metrics.get('layer_skip_reason')}"
        )
    if layer_slug == LAYER_04_RIM_BUNDLE_PLACEMENT:
        return (
            f"placed={metrics.get('selected_count')} "
            f"overlap_rejected={metrics.get('rejected_overlap_count')} "
            f"overlay_cells={metrics.get('overlay_occupied_cell_count')}"
        )
    if layer_slug == LAYER_05_INNER_PATTERN_FILL:
        return f"stub={metrics.get('stub', True)}"
    if layer_slug == LAYER_06_COMMIT_VALIDATE:
        return f"stub={metrics.get('stub', True)}"
    return f"outcome={outcome.value}"


__all__ = [
    "LAYER_BEHAVIOR_BY_SLUG",
    "format_layer_summary_line",
    "layer_behavior_for_slug",
]
