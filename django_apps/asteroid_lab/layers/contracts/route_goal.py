"""Shim: relocated to shapez2_factory.application.asteroid_lab.layers.contracts.route_goal."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    ROUTE_GOAL_PRIORITY_REQUIRED,
    ROUTE_GOAL_PRIORITY_SPARE,
    RouteGoal,
    RouteGoalKind,
    build_layer03_route_goals,
    transport_kind_for_connector,
)

__all__ = [
    "ROUTE_GOAL_PRIORITY_REQUIRED",
    "ROUTE_GOAL_PRIORITY_SPARE",
    "RouteGoal",
    "RouteGoalKind",
    "build_layer03_route_goals",
    "transport_kind_for_connector",
]
