"""Expand L3 route-probe walkable surface to reach exterior-lane L2 connectors."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.slots import (
    EXTERIOR_LANE_OFFSET,
    field_bounding_box,
    generate_exterior_lane_coords_for_edge,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import BBox, Coord, bbox_from_coords


def _add_non_field(out: set[Coord], coord: Coord, field_cells: frozenset[Coord]) -> None:
    if coord not in field_cells:
        out.add(coord)


def _bridge_and_lane_cells_for_edges(
    *,
    field_bbox: tuple[int, int, int, int],
    walkable_bbox: BBox,
    field_cells: frozenset[Coord],
    edges: frozenset[CardinalEdge],
) -> frozenset[Coord]:
    """O(perimeter * offset) exterior strips — not O(bbox area) fill."""

    min_x, min_y, max_x, max_y = field_bbox
    off = EXTERIOR_LANE_OFFSET
    wx0, wy0, wx1, wy1 = (
        walkable_bbox.min_x,
        walkable_bbox.min_y,
        walkable_bbox.max_x,
        walkable_bbox.max_y,
    )
    cells: set[Coord] = set()

    for edge in edges:
        for coord in generate_exterior_lane_coords_for_edge(
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
            edge=edge,
        ):
            _add_non_field(cells, coord, field_cells)

    if CardinalEdge.EAST in edges:
        lane_y = max_y + off
        east_end = max_x + off
        for x in range(wx1 + 1, east_end + 1):
            for y in range(wy0, wy1 + 1):
                _add_non_field(cells, (x, y), field_cells)
        for x in range(wx0, east_end + 1):
            _add_non_field(cells, (x, lane_y), field_cells)

    if CardinalEdge.WEST in edges:
        lane_x = min_x - off
        for x in range(lane_x, wx0):
            for y in range(wy0, wy1 + 1):
                _add_non_field(cells, (x, y), field_cells)
        for y in range(wy0, max_y + off + 1):
            _add_non_field(cells, (lane_x, y), field_cells)

    if CardinalEdge.NORTH in edges:
        lane_y = min_y - off
        for y in range(lane_y, wy0):
            for x in range(wx0, wx1 + 1):
                _add_non_field(cells, (x, y), field_cells)
        for x in range(min_x - off, max_x + off + 1):
            _add_non_field(cells, (x, lane_y), field_cells)

    if CardinalEdge.SOUTH in edges:
        lane_y = min_y - off
        for y in range(lane_y, wy0):
            for x in range(wx0, wx1 + 1):
                _add_non_field(cells, (x, y), field_cells)
        for x in range(wx0, max_x + off + 1):
            _add_non_field(cells, (x, lane_y), field_cells)

    return frozenset(cells)


def build_layer03_routing_walkable(
    *,
    field_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord],
    exterior_plan: ExteriorConnectionPlan | None,
) -> tuple[frozenset[Coord], BBox]:
    """Union reconstruction walkable with lane strips to exterior L2 connector goals."""

    base_walkable = field_cells | external_void_cells
    if exterior_plan is None or not exterior_plan.planned_connectors:
        if not base_walkable:
            empty_bbox = bbox_from_coords(frozenset())
            return frozenset(), empty_bbox
        return frozenset(base_walkable), bbox_from_coords(base_walkable)

    connector_coords = frozenset(
        connector.void_coord for connector in exterior_plan.planned_connectors
    )
    outside_connectors = connector_coords - base_walkable
    if not outside_connectors:
        return frozenset(base_walkable), bbox_from_coords(base_walkable)

    walkable_bbox = bbox_from_coords(base_walkable)
    edges_with_connectors = frozenset(
        connector.edge for connector in exterior_plan.planned_connectors
    )
    extension = _bridge_and_lane_cells_for_edges(
        field_bbox=field_bounding_box(field_cells),
        walkable_bbox=walkable_bbox,
        field_cells=field_cells,
        edges=edges_with_connectors,
    )
    base_walkable = base_walkable | extension
    return frozenset(base_walkable), bbox_from_coords(base_walkable)


__all__ = ["build_layer03_routing_walkable"]
