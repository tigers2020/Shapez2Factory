"""Bounded weighted install/search surface for L3 route probe (not transport network)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.snapshots.grid_contract import BBox, Coord

EXTERIOR_ROUTE_COST = 1
FIELD_ROUTE_COST = 25


@dataclass(frozen=True, slots=True)
class WeightedTransportRouteDomain:
    """Install surface inside search_bbox; walkable_cells MUST NOT be promoted to stubs."""

    search_bbox: BBox
    blocked_cells: frozenset[Coord]
    walkable_cells: frozenset[Coord]
    field_cost_cells: frozenset[Coord]

    def step_cost(self, coord: Coord) -> int | None:
        if coord not in self.walkable_cells:
            return None
        if coord in self.field_cost_cells:
            return FIELD_ROUTE_COST
        return EXTERIOR_ROUTE_COST


__all__ = [
    "EXTERIOR_ROUTE_COST",
    "FIELD_ROUTE_COST",
    "WeightedTransportRouteDomain",
]
