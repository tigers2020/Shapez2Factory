"""Small maps for rim anchor boundary-walk golden tests."""

from __future__ import annotations

from collections import deque

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord, neighbors4

# 5×5 field block at (2,2)..(6,6) with interior void at (4,4) — not external.
_FIELD_ORIGIN = 2
_FIELD_SIZE = 5
_INTERIOR_VOID = (4, 4)


def _field_cells_with_pocket() -> frozenset[Coord]:
    cells: set[Coord] = set()
    for x in range(_FIELD_ORIGIN, _FIELD_ORIGIN + _FIELD_SIZE):
        for y in range(_FIELD_ORIGIN, _FIELD_ORIGIN + _FIELD_SIZE):
            if (x, y) == _INTERIOR_VOID:
                continue
            cells.add((x, y))
    return frozenset(cells)


def _void_adjacent_to_field(field: frozenset[Coord]) -> frozenset[Coord]:
    adjacent: set[Coord] = set()
    for coord in field:
        for neighbor in neighbors4(coord):
            if neighbor not in field:
                adjacent.add(neighbor)
    return frozenset(adjacent)


def _external_void_cells(field: frozenset[Coord]) -> frozenset[Coord]:
    """Field-adjacent void reachable from outside (interior pocket void excluded)."""
    adjacent_void = _void_adjacent_to_field(field)
    min_x = min(c[0] for c in field)
    max_x = max(c[0] for c in field)
    min_y = min(c[1] for c in field)
    max_y = max(c[1] for c in field)
    seeds = [
        coord
        for coord in adjacent_void
        if coord[0] <= min_x or coord[0] >= max_x or coord[1] <= min_y or coord[1] >= max_y
    ]
    external: set[Coord] = set()
    queue: deque[Coord] = deque()
    for seed in seeds:
        queue.append(seed)
        external.add(seed)
    while queue:
        current = queue.popleft()
        for neighbor in neighbors4(current):
            if neighbor not in adjacent_void or neighbor in external:
                continue
            external.add(neighbor)
            queue.append(neighbor)
    return frozenset(external)


def rim_walk_pocket_complete_map() -> ReconstructionCompleteMap:
    field = _field_cells_with_pocket()
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=_external_void_cells(field),
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def rim_walk_full_5x5_complete_map() -> ReconstructionCompleteMap:
    cells: set[Coord] = set()
    for x in range(_FIELD_ORIGIN, _FIELD_ORIGIN + _FIELD_SIZE):
        for y in range(_FIELD_ORIGIN, _FIELD_ORIGIN + _FIELD_SIZE):
            cells.add((x, y))
    field = frozenset(cells)
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=_external_void_cells(field),
        coord_frame=CoordFrame.ISLAND_RAW,
    )


__all__ = [
    "rim_walk_full_5x5_complete_map",
    "rim_walk_pocket_complete_map",
]
