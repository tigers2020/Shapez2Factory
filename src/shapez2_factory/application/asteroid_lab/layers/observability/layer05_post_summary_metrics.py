"""Layer 05 transport routing post-summary metrics (canonical L5 slug)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    Layer05RoutePlan,
)
from shapez2_factory.application.asteroid_lab.layers.observability.layer04_post_summary_metrics import (  # noqa: E501
    build_layer04_transport_post_summary_metrics,
)


def build_layer05_transport_post_summary_metrics(plan: Layer05RoutePlan) -> dict[str, object]:
    return build_layer04_transport_post_summary_metrics(plan)


__all__ = ["build_layer05_transport_post_summary_metrics"]
