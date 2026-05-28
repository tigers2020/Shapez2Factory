"""Metrics wire serialization for exterior connector plans."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)

_EDGES_ORDER: tuple[CardinalEdge, ...] = (
    CardinalEdge.NORTH,
    CardinalEdge.EAST,
    CardinalEdge.SOUTH,
    CardinalEdge.WEST,
)


def exterior_connector_plan_to_metrics_dict(plan: ExteriorConnectionPlan) -> dict[str, Any]:
    counts_by_edge = {edge.value: 0 for edge in _EDGES_ORDER}
    for conn in plan.planned_connectors:
        counts_by_edge[conn.edge.value] += 1

    required_planned = sum(
        1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.REQUIRED
    )
    spare_planned = sum(
        1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.SPARE
    )

    return {
        "exterior_connector_plan": {
            "version": "exterior_connector_plan.v2",
            "slot_rule": plan.slot_rule,
            "placement_rule": plan.placement_rule,
            "rotation_rule": plan.rotation_rule,
            "rotation_convention": "R0_E_CW",
            "required_connector_count": plan.required_connector_count,
            "reference_connector_count": plan.reference_connector_count,
            "spare_connector_count": plan.spare_connector_count,
            "required_planned_count": required_planned,
            "spare_planned_count": spare_planned,
            "planned_connector_count": required_planned + spare_planned,
            "counts_by_edge": counts_by_edge,
            "planned_connectors": [
                {
                    "connector_id": c.connector_id,
                    "void_coord": {"x": c.void_coord[0], "y": c.void_coord[1]},
                    "edge": c.edge.value,
                    "layout_t": c.layout_t,
                    "rotation": c.rotation,
                    "capacity_per_min": str(c.capacity_per_min),
                    "role": c.role.value,
                    "coords": [{"x": xy[0], "y": xy[1]} for xy in c.coords],
                }
                for c in plan.planned_connectors
            ],
            "unmet_reason": plan.unmet_reason.value if plan.unmet_reason else None,
        }
    }


__all__ = ["exterior_connector_plan_to_metrics_dict"]
