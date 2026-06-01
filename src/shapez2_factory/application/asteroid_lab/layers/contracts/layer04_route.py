"""Deprecated import path; canonical transport contracts live in ``layer05_route``."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    DEPRECATED_LAYER04_ROUTE_PLAN_VERSION,
    CommittedRoute,
    Layer05Failure,
    Layer05FailureReason,
    Layer05Metrics,
    Layer05RoutePlan,
    Layer05SourceView,
    ProjectedTransportTile,
    RouteGroupSummary,
)

LAYER04_ROUTE_PLAN_VERSION = DEPRECATED_LAYER04_ROUTE_PLAN_VERSION
Layer04FailureReason = Layer05FailureReason
Layer04SourceView = Layer05SourceView
Layer04Failure = Layer05Failure
Layer04Metrics = Layer05Metrics
Layer04RoutePlan = Layer05RoutePlan

__all__ = [
    "LAYER04_ROUTE_PLAN_VERSION",
    "CommittedRoute",
    "Layer04Failure",
    "Layer04FailureReason",
    "Layer04Metrics",
    "Layer04RoutePlan",
    "Layer04SourceView",
    "ProjectedTransportTile",
    "RouteGroupSummary",
]
