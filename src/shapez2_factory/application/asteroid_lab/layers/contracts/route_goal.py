"""Layer 03 route goals derived from L2 ExteriorConnectionPlan."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnector,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import TransportKind
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

ROUTE_GOAL_PRIORITY_REQUIRED = 0
ROUTE_GOAL_PRIORITY_SPARE = 10


class RouteGoalKind(StrEnum):
    EXTERIOR_CONNECTOR_VOID = "exterior_connector_void"


@dataclass(frozen=True, slots=True)
class RouteGoal:
    goal_id: str
    kind: RouteGoalKind
    coord: Coord
    transport_kind: TransportKind
    priority: int
    connector_role: ExteriorConnectorRole


def transport_kind_for_connector(connector: ExteriorConnector) -> TransportKind:
    if connector.layout_t.startswith("SpacePipe"):
        return TransportKind.FLUID_PIPE
    return TransportKind.SHAPE_BELT


def build_layer03_route_goals(
    plan: ExteriorConnectionPlan,
    *,
    transport_kind: TransportKind,
) -> tuple[RouteGoal, ...]:
    goals: list[RouteGoal] = []
    for connector in plan.planned_connectors:
        if transport_kind_for_connector(connector) != transport_kind:
            continue
        priority = (
            ROUTE_GOAL_PRIORITY_REQUIRED
            if connector.role is ExteriorConnectorRole.REQUIRED
            else ROUTE_GOAL_PRIORITY_SPARE
        )
        goals.append(
            RouteGoal(
                goal_id=connector.connector_id,
                kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
                coord=connector.void_coord,
                transport_kind=transport_kind,
                priority=priority,
                connector_role=connector.role,
            )
        )
    goals.sort(key=lambda g: (g.priority, g.goal_id))
    return tuple(goals)


__all__ = [
    "ROUTE_GOAL_PRIORITY_REQUIRED",
    "ROUTE_GOAL_PRIORITY_SPARE",
    "RouteGoal",
    "RouteGoalKind",
    "build_layer03_route_goals",
    "transport_kind_for_connector",
]
