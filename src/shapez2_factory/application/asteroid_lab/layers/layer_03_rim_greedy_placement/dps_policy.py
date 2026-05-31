"""Greedy-specific weighted route domain for pass1 DPS probes."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.weighted_transport_route_domain import (  # noqa: E501
    WeightedTransportRouteDomain,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import BBox, Coord, cells_in_bbox
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def build_greedy_route_domain(
    *,
    complete_map: ReconstructionCompleteMap,
    search_bbox: BBox,
    occupied_equipment_cells: frozenset[Coord],
) -> WeightedTransportRouteDomain:
    """Walkable = field ∪ external_void inside bbox minus committed equipment (hard)."""
    field_cells = complete_map.field_cells
    external_void = complete_map.external_void_cells
    in_bbox = cells_in_bbox(search_bbox)
    walkable = frozenset(
        coord
        for coord in in_bbox
        if coord in field_cells or coord in external_void
        if coord not in occupied_equipment_cells
    )
    field_cost = frozenset(coord for coord in walkable if coord in field_cells)
    return WeightedTransportRouteDomain(
        search_bbox=search_bbox,
        blocked_cells=occupied_equipment_cells,
        walkable_cells=walkable,
        field_cost_cells=field_cost,
    )


__all__ = ["build_greedy_route_domain"]
