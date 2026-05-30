"""Contracts for integrated rim greedy placement (L3/L4 supersede)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_03_RIM_MINING_BUNDLES,
    LAYERS_02_TO_06_ACTIVE,
)
from django_apps.asteroid_lab.layers.contracts.rim_greedy import (
    LAYER_03_GREEDY_SOURCE,
    RimGreedyRejectReason,
    build_empty_integrated_rim_greedy_result,
)


def test_active_runner_tuple_uses_greedy_slug_only() -> None:
    assert LAYER_03_RIM_GREEDY_PLACEMENT in LAYERS_02_TO_06_ACTIVE
    assert LAYER_03_RIM_MINING_BUNDLES not in LAYERS_02_TO_06_ACTIVE


def test_empty_result_has_canonical_overlay_source() -> None:
    result = build_empty_integrated_rim_greedy_result(
        layer_skip_reason="missing_exterior_connection_plan",
    )
    assert result.provisional_overlay.source_layer == LAYER_03_GREEDY_SOURCE
    assert len(result.observability_events) == 2
    assert result.metrics.canonical_layer_slug == LAYER_03_RIM_GREEDY_PLACEMENT
    assert result.append_result.placement_count == 0


def test_reject_reason_is_strenum() -> None:
    assert RimGreedyRejectReason.DPS_UNREACHABLE.value == "DPS_UNREACHABLE"
