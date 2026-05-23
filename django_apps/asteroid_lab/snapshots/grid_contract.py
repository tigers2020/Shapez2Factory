"""Integer topology grid helpers (reconstruction + optimization + lab).

``Coord`` is ``tuple[int, int]`` in the active frame. Lab RTTP uses raw island
``(x, y)`` coordinates by default. Use ``neighbors4`` for 4-neighbor steps.
"""

from __future__ import annotations

from dataclasses import dataclass

Coord = tuple[int, int]

OUTER_VOID_PADDING = 10


@dataclass(frozen=True, slots=True)
class BBox:
    """Inclusive topology bounding box in the active raw coordinate frame."""

    min_x: int
    max_x: int
    min_y: int
    max_y: int


def bbox_from_coords(coords: frozenset[Coord]) -> BBox:
    """Inclusive bbox over ``coords``; empty becomes ``BBox(0, 0, 0, 0)``."""

    if not coords:
        return BBox(0, 0, 0, 0)
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return BBox(min(xs), max(xs), min(ys), max(ys))


def expand_bbox(bb: BBox, padding: int) -> BBox:
    """Expand inclusive bbox by ``padding`` cells on each side."""

    return BBox(
        bb.min_x - padding,
        bb.max_x + padding,
        bb.min_y - padding,
        bb.max_y + padding,
    )


def cells_in_bbox(bb: BBox) -> frozenset[Coord]:
    """All integer grid coords inside inclusive ``bb``."""

    return frozenset(
        (x, y)
        for x in range(bb.min_x, bb.max_x + 1)
        for y in range(bb.min_y, bb.max_y + 1)
    )


def neighbors4(coord: Coord) -> tuple[Coord, Coord, Coord, Coord]:
    """Standard 4-neighbors on the active integer topology grid."""

    x, y = coord
    return ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))


__all__ = [
    "BBox",
    "Coord",
    "OUTER_VOID_PADDING",
    "bbox_from_coords",
    "cells_in_bbox",
    "expand_bbox",
    "neighbors4",
]
