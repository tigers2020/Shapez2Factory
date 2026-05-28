"""Synthetic ReconstructionCompleteMap fixtures for Layer 02 tests."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def make_complete_map(
    *,
    field_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord],
) -> ReconstructionCompleteMap:
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field_cells,
        shape_field_cell_count=len(field_cells),
        fluid_field_cell_count=0,
        external_void_cells=external_void_cells,
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def build_rect_field_with_void_shell(
    *,
    width: int,
    height: int,
    void_pad: int,
) -> ReconstructionCompleteMap:
    field = frozenset((x, y) for x in range(width) for y in range(height))
    void: set[Coord] = set()
    for x in range(-void_pad, width + void_pad):
        for y in range(-void_pad, height + void_pad):
            if (x, y) not in field:
                void.add((x, y))
    return make_complete_map(field_cells=field, external_void_cells=frozenset(void))
