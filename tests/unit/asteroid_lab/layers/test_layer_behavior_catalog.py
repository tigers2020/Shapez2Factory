"""Layer behavior catalog summary formatters."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer_post_summary import LayerPostSummaryOutcome
from django_apps.asteroid_lab.layers.contracts.layer_slugs import LAYER_03_RIM_GREEDY_PLACEMENT
from django_apps.asteroid_lab.layers.observability.layer_behavior_catalog import (
    format_layer_summary_line,
    layer_behavior_for_slug,
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
