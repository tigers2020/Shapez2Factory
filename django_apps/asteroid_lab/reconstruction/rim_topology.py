"""Mineable field rim coords (reconstruction layer; not optimization)."""

from __future__ import annotations

from django_apps.asteroid_lab.snapshots.grid_contract import Coord, neighbors4


def field_rim_cells(field_cells: frozenset[Coord]) -> frozenset[Coord]:
    """Field cells with at least one 4-neighbor outside ``field_cells``."""

    rim: set[Coord] = set()
    for coord in field_cells:
        if any(neighbor not in field_cells for neighbor in neighbors4(coord)):
            rim.add(coord)
    return frozenset(rim)


__all__ = ["field_rim_cells"]
