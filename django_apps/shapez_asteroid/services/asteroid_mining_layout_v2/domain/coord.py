"""
Integer grid coordinates and bounding boxes.

Project convention (blueprint grid): ``Coord.x`` must never be ``0``; see
``documents/research`` and architecture rules. v2 enforces that at validation time;
this module only defines types.
"""

from __future__ import annotations

from dataclasses import dataclass

type BlueprintCell = tuple[int, int]


@dataclass(frozen=True, slots=True)
class Coord:
    """Blueprint (X, Y) cell; ``x == 0`` is illegal at solver boundaries (asserted later)."""

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


def as_blueprint_cell(value: Coord | BlueprintCell) -> BlueprintCell:
    """Normalize ``Coord`` or legacy ``(x, y)`` tuple for sets and routing helpers."""
    if isinstance(value, Coord):
        return value.as_tuple()
    return value
