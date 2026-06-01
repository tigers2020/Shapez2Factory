"""Layer 04 transport routing post-summary metrics (pure core)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04RoutePlan,
)


def build_layer04_transport_post_summary_metrics(plan: Layer04RoutePlan) -> dict[str, object]:
    metrics = plan.metrics
    failure_reasons = [f.reason.value for f in plan.failures]
    return {
        "resource_kind": plan.resource_kind,
        "transport_kind": plan.transport_kind,
        "source_count": metrics.source_count,
        "routed_source_count": metrics.routed_source_count,
        "failed_source_count": metrics.failed_source_count,
        "route_count": len(plan.routes),
        "group_count": len(plan.groups),
        "transport_tile_count": len(plan.transport_tiles),
        "total_route_cells": metrics.total_route_cells,
        "total_route_cost": metrics.total_route_cost,
        "failure_reasons": failure_reasons,
    }


__all__ = ["build_layer04_transport_post_summary_metrics"]
