"""
Single-cell blueprint coordinates and atomic X-axis rules.

There is **no** column at ``x == 0``; east/west adjacency jumps ``-1 ↔ 1``.
All horizontal motion goes through ``step_x`` / ``neighbor`` — never ``coord.x + dx``.

This module must **not** import ``grid`` or encode bbox / set / mask operations; those
live in ``domain.grid``.
"""

from __future__ import annotations

from dataclasses import dataclass

type BlueprintCell = tuple[int, int]
type Direction = tuple[int, int]


@dataclass(frozen=True, slots=True)
class Coord:
    """One blueprint lattice cell."""

    x: int
    y: int

    def as_tuple(self) -> BlueprintCell:
        return (self.x, self.y)


@dataclass(frozen=True, slots=True)
class BBox:
    """Axis-aligned bounding box in blueprint cell coordinates."""

    min_x: int
    min_y: int
    max_x: int
    max_y: int


def is_physical_x(x: int) -> bool:
    """True iff ``x`` is a valid blueprint column index (``x != 0``)."""

    return x != 0


def is_physical_coord(coord: Coord) -> bool:
    return is_physical_x(coord.x)


def step_x(x: int, dx: int) -> int:
    """One horizontal step on the no-``x==0`` lattice; never returns ``0``."""

    if dx == 0:
        return x
    if dx not in (-1, 1):
        msg = "step_x dx must be -1, 0, or 1"
        raise ValueError(msg)
    if x == 0:
        msg = "step_x from illegal x==0"
        raise ValueError(msg)
    if dx == -1:
        return -1 if x == 1 else x - 1
    return 1 if x == -1 else x + 1


def neighbor(coord: Coord, direction: Direction) -> Coord:
    """One cardinal step ``direction`` as ``(dx, dy)``; not diagonal."""

    dx, dy = direction
    if dx != 0 and dy != 0:
        msg = "neighbor expects a cardinal direction"
        raise ValueError(msg)
    if dx:
        return Coord(step_x(coord.x, dx), coord.y)
    return Coord(coord.x, coord.y + dy)


def as_blueprint_cell(value: Coord | BlueprintCell) -> BlueprintCell:
    """Normalize ``Coord`` or legacy ``(x, y)`` tuple for sets and routing helpers."""

    if isinstance(value, Coord):
        return value.as_tuple()
    return value


__all__ = [
    "BBox",
    "BlueprintCell",
    "Coord",
    "Direction",
    "as_blueprint_cell",
    "is_physical_coord",
    "is_physical_x",
    "neighbor",
    "step_x",
]
