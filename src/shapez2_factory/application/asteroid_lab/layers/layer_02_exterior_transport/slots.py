"""VOID_DEEP_SLOTS_V1 ??exterior void slot catalog from reconstruction-complete map."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.rim_topology import field_rim_cells

VOID_DEPTH_MIN = 5
RIM_VOID_DEPTH = 1
EXTERIOR_LANE_OFFSET = 12
CONNECTOR_LANE_SPACING = 2
MAX_LANE_SLOTS_PER_EDGE = 64

_EDGES_ORDER: tuple[CardinalEdge, ...] = (
    CardinalEdge.NORTH,
    CardinalEdge.EAST,
    CardinalEdge.SOUTH,
    CardinalEdge.WEST,
)

_NEIGHBOR_DELTAS_NESW: tuple[tuple[CardinalEdge, tuple[int, int]], ...] = (
    (CardinalEdge.NORTH, (0, -1)),
    (CardinalEdge.EAST, (1, 0)),
    (CardinalEdge.SOUTH, (0, 1)),
    (CardinalEdge.WEST, (-1, 0)),
)

_EDGE_DELTA: dict[CardinalEdge, tuple[int, int]] = {
    edge: delta for edge, delta in _NEIGHBOR_DELTAS_NESW
}

_EDGE_SORT_KEY = {
    CardinalEdge.NORTH: lambda c: c[0],
    CardinalEdge.EAST: lambda c: c[1],
    CardinalEdge.SOUTH: lambda c: -c[0],
    CardinalEdge.WEST: lambda c: -c[1],
}


@dataclass(frozen=True, slots=True)
class VoidDepthEntry:
    void_coord: Coord
    depth: int
    source_edge: CardinalEdge
    source_field: Coord


def compute_void_depth_entries(
    complete_map: ReconstructionCompleteMap,
) -> dict[Coord, VoidDepthEntry]:
    field_cells = complete_map.field_cells
    external_void = complete_map.external_void_cells
    outer_rim = field_rim_cells(field_cells)

    entries: dict[Coord, VoidDepthEntry] = {}
    queue: deque[Coord] = deque()

    for edge in _EDGES_ORDER:
        for source_field in sorted(outer_rim):
            dx, dy = _EDGE_DELTA[edge]
            seed = (source_field[0] + dx, source_field[1] + dy)
            if seed not in external_void or seed in entries:
                continue
            entries[seed] = VoidDepthEntry(
                void_coord=seed,
                depth=1,
                source_edge=edge,
                source_field=source_field,
            )
            queue.append(seed)

    while queue:
        current = queue.popleft()
        current_entry = entries[current]
        next_depth = current_entry.depth + 1
        for _edge, (dx, dy) in _NEIGHBOR_DELTAS_NESW:
            neighbor = (current[0] + dx, current[1] + dy)
            if neighbor not in external_void or neighbor in entries:
                continue
            entries[neighbor] = VoidDepthEntry(
                void_coord=neighbor,
                depth=next_depth,
                source_edge=current_entry.source_edge,
                source_field=current_entry.source_field,
            )
            queue.append(neighbor)

    return entries


def build_candidate_slots_by_edge(
    complete_map: ReconstructionCompleteMap,
) -> dict[CardinalEdge, list[Coord]]:
    entries = compute_void_depth_entries(complete_map)
    by_edge: dict[CardinalEdge, list[Coord]] = {edge: [] for edge in _EDGES_ORDER}
    for coord, entry in entries.items():
        if entry.depth < VOID_DEPTH_MIN:
            continue
        by_edge[entry.source_edge].append(coord)
    for edge in _EDGES_ORDER:
        by_edge[edge].sort(key=_EDGE_SORT_KEY[edge])
    return by_edge


def parse_allowed_cardinal_edges(
    raw: object,
    *,
    default: frozenset[CardinalEdge] | None = None,
) -> frozenset[CardinalEdge]:
    """Normalize UI/config edge list; empty or invalid input falls back to all edges."""

    if default is None:
        default = frozenset(_EDGES_ORDER)
    if raw is None:
        return default
    if not isinstance(raw, (list, tuple)):
        return default
    parsed: set[CardinalEdge] = set()
    for item in raw:
        try:
            parsed.add(CardinalEdge(str(item).lower()))
        except ValueError:
            continue
    return frozenset(parsed) if parsed else default


def field_bounding_box(field_cells: frozenset[Coord]) -> tuple[int, int, int, int]:
    xs = [coord[0] for coord in field_cells]
    ys = [coord[1] for coord in field_cells]
    return min(xs), min(ys), max(xs), max(ys)


def _connector_coord_is_placeable(
    complete_map: ReconstructionCompleteMap,
    coord: Coord,
) -> bool:
    return coord not in complete_map.field_cells


def _generate_lane_coords_for_edge(
    *,
    min_x: int,
    min_y: int,
    max_x: int,
    max_y: int,
    edge: CardinalEdge,
    limit: int,
) -> list[Coord]:
    off = EXTERIOR_LANE_OFFSET
    spacing = CONNECTOR_LANE_SPACING
    coords: list[Coord] = []
    if edge is CardinalEdge.EAST:
        lane_y = max_y + off
        start_x = max_x + off
        for index in range(limit):
            coords.append((start_x - spacing * index, lane_y))
    elif edge is CardinalEdge.NORTH:
        lane_x = min_x - off
        start_y = min_y - off
        for index in range(limit):
            coords.append((lane_x + spacing * index, start_y))
    elif edge is CardinalEdge.WEST:
        lane_x = min_x - off
        start_y = max_y + off
        for index in range(limit):
            coords.append((lane_x, start_y - spacing * index))
    elif edge is CardinalEdge.SOUTH:
        lane_y = min_y - off
        start_x = max_x + off
        for index in range(limit):
            coords.append((start_x - spacing * index, lane_y))
    return coords


def build_exterior_lane_slots_by_edge(
    complete_map: ReconstructionCompleteMap,
    *,
    allowed_edges: frozenset[CardinalEdge] | None = None,
) -> dict[CardinalEdge, list[Coord]]:
    """Fixed exterior lanes offset from field bbox (not rim-adjacent void cells)."""

    if allowed_edges is None:
        allowed_edges = frozenset(_EDGES_ORDER)
    min_x, min_y, max_x, max_y = field_bounding_box(complete_map.field_cells)
    by_edge: dict[CardinalEdge, list[Coord]] = {edge: [] for edge in _EDGES_ORDER}
    for edge in _EDGES_ORDER:
        if edge not in allowed_edges:
            continue
        raw_coords = _generate_lane_coords_for_edge(
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
            edge=edge,
            limit=MAX_LANE_SLOTS_PER_EDGE,
        )
        by_edge[edge] = [
            coord
            for coord in raw_coords
            if _connector_coord_is_placeable(complete_map, coord)
        ]
    return by_edge


def build_rim_edge_slots_by_edge(
    complete_map: ReconstructionCompleteMap,
    *,
    allowed_edges: frozenset[CardinalEdge] | None = None,
) -> dict[CardinalEdge, list[Coord]]:
    """Depth-1 void cells directly outside the field rim, filtered by allowed edges."""

    if allowed_edges is None:
        allowed_edges = frozenset(_EDGES_ORDER)
    entries = compute_void_depth_entries(complete_map)
    by_edge: dict[CardinalEdge, list[Coord]] = {edge: [] for edge in _EDGES_ORDER}
    for coord, entry in entries.items():
        if entry.depth != RIM_VOID_DEPTH:
            continue
        if entry.source_edge not in allowed_edges:
            continue
        by_edge[entry.source_edge].append(coord)
    for edge in _EDGES_ORDER:
        by_edge[edge].sort(key=_EDGE_SORT_KEY[edge])
    return by_edge


def generate_exterior_lane_coords_for_edge(
    *,
    min_x: int,
    min_y: int,
    max_x: int,
    max_y: int,
    edge: CardinalEdge,
    limit: int = MAX_LANE_SLOTS_PER_EDGE,
) -> tuple[Coord, ...]:
    """Deterministic exterior-lane slot coords for one cardinal edge."""

    return tuple(
        _generate_lane_coords_for_edge(
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
            edge=edge,
            limit=limit,
        )
    )


__all__ = [
    "CONNECTOR_LANE_SPACING",
    "EXTERIOR_LANE_OFFSET",
    "RIM_VOID_DEPTH",
    "VOID_DEPTH_MIN",
    "VoidDepthEntry",
    "build_candidate_slots_by_edge",
    "build_exterior_lane_slots_by_edge",
    "build_rim_edge_slots_by_edge",
    "compute_void_depth_entries",
    "field_bounding_box",
    "generate_exterior_lane_coords_for_edge",
    "parse_allowed_cardinal_edges",
]
