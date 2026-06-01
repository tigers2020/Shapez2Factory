"""L4 weighted route search domain (separate from L3 ``WeightedTransportRouteDomain``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from shapez2_factory.domain.asteroid_lab.grid_contract import BBox, Coord, bbox_from_coords
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

L4TerrainKind = Literal["void", "asteroid_field", "e", "m"]

L4_CELL_WEIGHT: dict[L4TerrainKind, int] = {
    "void": 1,
    "asteroid_field": 5,
    "e": 10,
    "m": 20,
}


def terrain_kind_at(
    coord: Coord,
    *,
    field_cells: frozenset[Coord],
    void_cells: frozenset[Coord],
    miner_cells: frozenset[Coord],
    extension_cells: frozenset[Coord],
) -> L4TerrainKind | None:
    if coord in miner_cells:
        return "m"
    if coord in extension_cells:
        return "e"
    if coord in field_cells:
        return "asteroid_field"
    if coord in void_cells:
        return "void"
    return None


@dataclass(frozen=True, slots=True)
class L4RouteSearchDomain:
    search_bbox: BBox
    walkable_cells: frozenset[Coord]
    terrain_at: dict[Coord, L4TerrainKind]

    def step_cost(self, coord: Coord) -> int | None:
        kind = self.terrain_at.get(coord)
        if kind is None:
            return None
        return L4_CELL_WEIGHT[kind]


def build_l4_route_search_domain(
    *,
    complete_map: ReconstructionCompleteMap,
    miner_cells: frozenset[Coord],
    extension_cells: frozenset[Coord],
) -> L4RouteSearchDomain:
    field_cells = complete_map.field_cells
    void_cells = complete_map.external_void_cells - field_cells
    equipment = miner_cells | extension_cells
    walkable = void_cells | field_cells | equipment
    terrain_at: dict[Coord, L4TerrainKind] = {}
    for coord in walkable:
        kind = terrain_kind_at(
            coord,
            field_cells=field_cells,
            void_cells=void_cells,
            miner_cells=miner_cells,
            extension_cells=extension_cells,
        )
        if kind is not None:
            terrain_at[coord] = kind
    bbox = bbox_from_coords(walkable) if walkable else bbox_from_coords(frozenset({(0, 0)}))
    return L4RouteSearchDomain(
        search_bbox=bbox,
        walkable_cells=walkable,
        terrain_at=terrain_at,
    )


__all__ = [
    "L4_CELL_WEIGHT",
    "L4RouteSearchDomain",
    "L4TerrainKind",
    "build_l4_route_search_domain",
    "terrain_kind_at",
]
