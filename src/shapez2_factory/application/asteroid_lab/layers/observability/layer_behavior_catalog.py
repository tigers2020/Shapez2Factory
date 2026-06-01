"""Per-layer behavior patterns and one-line summary formatters (observability only)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer_post_summary import (
    LayerPostSummaryOutcome,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_01_RECONSTRUCTION,
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_04_TRANSPORT_ROUTING,
    LAYER_05_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
    LAYER_06_COMMIT_VALIDATE,
    resolve_canonical_layer_slug,
)

LAYER_BEHAVIOR_BY_SLUG: dict[str, str] = {
    LAYER_01_RECONSTRUCTION: (
        "Deconstruct snapshot ??topology reconstruction ??ReconstructionCompleteMap "
        "(field cells, external void, capacity envelope)."
    ),
    LAYER_02_EXTERIOR_TRANSPORT: (
        "Plan required and spare exterior connectors on void rim slots; "
        "emit belt/pipe stubs toward the shape field at terrain throughput target."
    ),
    LAYER_03_RIM_GREEDY_PLACEMENT: (
        "Traverse ordered outer-rim anchors; greedy provisional M/E placement; "
        "DPS reachability; route reservation; pass2 score across deterministic variants."
    ),
    LAYER_04_INNER_PATTERN_FILL: (
        "Fill interior pattern from complete_map + provisional overlay "
        "(stub; no route plan input; runs before transport)."
    ),
    LAYER_05_TRANSPORT_ROUTING: (
        "Merge-aware weighted routes from L3 stubs to L2 connectors; "
        "catalog-backed belt/pipe tile projection (canonical L5)."
    ),
    # Deprecated slug literals (read-compat; same behavior text as canonical).
    LAYER_05_INNER_PATTERN_FILL: (
        "Fill interior pattern from complete_map + provisional overlay "
        "(deprecated slug; canonical layer_04_inner_pattern_fill)."
    ),
    LAYER_04_TRANSPORT_ROUTING: (
        "Transport routing (deprecated slug; canonical layer_05_transport_routing)."
    ),
    LAYER_06_COMMIT_VALIDATE: (
        "Re-probe route domain and commit ROUTED_CONFIRMED placements; "
        "structural validation gate (stub in PR-3c)."
    ),
}


def layer_behavior_for_slug(layer_slug: str) -> str:
    canonical = resolve_canonical_layer_slug(layer_slug)
    return LAYER_BEHAVIOR_BY_SLUG.get(
        canonical,
        LAYER_BEHAVIOR_BY_SLUG.get(
            layer_slug,
            "Layer stack step (behavior catalog entry not defined).",
        ),
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
    if layer_slug == LAYER_03_RIM_GREEDY_PLACEMENT:
        return (
            f"rim_anchors={metrics.get('rim_anchor_count')} "
            f"committed={metrics.get('committed_placement_count')} "
            f"variant={metrics.get('winning_variant_id')} "
            f"skip={metrics.get('layer_skip_reason')}"
        )
    canonical = resolve_canonical_layer_slug(layer_slug)
    if canonical == LAYER_04_INNER_PATTERN_FILL:
        return (
            f"interior_cells={metrics.get('interior_occupied_cell_count', 0)} "
            f"stub={metrics.get('stub', True)}"
        )
    if canonical == LAYER_05_TRANSPORT_ROUTING:
        return (
            f"sources={metrics.get('source_count')} "
            f"routed={metrics.get('routed_source_count')} "
            f"tiles={metrics.get('transport_tile_count')}"
        )
    if layer_slug == LAYER_06_COMMIT_VALIDATE:
        return f"stub={metrics.get('stub', True)}"
    return f"outcome={outcome.value}"


__all__ = [
    "LAYER_BEHAVIOR_BY_SLUG",
    "format_layer_summary_line",
    "layer_behavior_for_slug",
]
