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


__all__ = [
    "VOID_DEPTH_MIN",
    "VoidDepthEntry",
    "build_candidate_slots_by_edge",
    "compute_void_depth_entries",
]
