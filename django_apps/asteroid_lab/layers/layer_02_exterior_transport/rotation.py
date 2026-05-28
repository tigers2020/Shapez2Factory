"""R0_E_CW rotation and fieldward-facing mapping for exterior connectors."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge

ROTATION_R0_E_CW = {
    "east": 0,
    "south": 1,
    "west": 2,
    "north": 3,
}

FIELDWARD_ROTATION_BY_EDGE = {
    CardinalEdge.NORTH: 1,
    CardinalEdge.EAST: 2,
    CardinalEdge.SOUTH: 3,
    CardinalEdge.WEST: 0,
}

__all__ = ["FIELDWARD_ROTATION_BY_EDGE", "ROTATION_R0_E_CW"]
