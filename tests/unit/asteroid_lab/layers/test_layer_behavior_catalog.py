"""Layer behavior catalog summary formatters."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.observability.layer_behavior_catalog import (
    format_layer_summary_line,
    layer_behavior_for_slug,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_post_summary import (
    LayerPostSummaryOutcome,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_04_TRANSPORT_ROUTING,
    LAYER_05_TRANSPORT_ROUTING,
)


def test_layer03_summary_line_includes_skip_reason() -> None:
    text = format_layer_summary_line(
        LAYER_03_RIM_GREEDY_PLACEMENT,
        outcome=LayerPostSummaryOutcome.COMPLETED,
        metrics={
            "rim_anchor_count": 81,
            "committed_placement_count": 0,
            "winning_variant_id": "",
            "layer_skip_reason": "missing_exterior_connection_plan",
        },
    )
    assert "rim_anchors=81" in text
    assert "skip=missing_exterior_connection_plan" in text
    assert layer_behavior_for_slug(LAYER_03_RIM_GREEDY_PLACEMENT)
    assert "interior" in layer_behavior_for_slug(LAYER_04_INNER_PATTERN_FILL).lower()
    assert "routes" in layer_behavior_for_slug(LAYER_05_TRANSPORT_ROUTING).lower()
    assert layer_behavior_for_slug(LAYER_04_TRANSPORT_ROUTING) == layer_behavior_for_slug(
        LAYER_05_TRANSPORT_ROUTING,
    )
