"""Dense Server X/Y grid helpers (Phase 1 coordinate contract)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.enums import Direction

Coord = tuple[int, int]


def neighbors4_server(coord: Coord) -> tuple[Coord, Coord, Coord, Coord]:
    """Standard 4-neighbors on the dense integer grid (includes ``x == 0``)."""

    x, y = coord
    return ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))


def cardinal_unit_toward(src: Coord, dst: Coord) -> Direction:
    """Single cardinal step from ``src`` toward ``dst`` (must differ on exactly one axis)."""

    sx, sy = src
    dx, dy = dst
    if src == dst:
        msg = "cardinal_unit_toward requires src != dst"
        raise ValueError(msg)
    if sx != dx and sy != dy:
        msg = "cardinal_unit_toward requires Manhattan-aligned coords"
        raise ValueError(msg)
    if dx > sx:
        return Direction.E
    if dx < sx:
        return Direction.W
    if dy > sy:
        return Direction.S
    return Direction.N
