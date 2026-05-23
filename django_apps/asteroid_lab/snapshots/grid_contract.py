"""Integer topology grid helpers (reconstruction + optimization + lab).

``Coord`` is ``tuple[int, int]`` in the active frame: island-local ``(x, y)`` when
``OptimizationInput.coord_frame`` is ``ISLAND_RAW`` (PR-F default for lab RTTP),
or legacy server-dense keys when ``SERVER_DENSE``. Use ``neighbors4`` for
4-neighbor steps; ``neighbors4_server`` is a deprecated alias.
"""

from __future__ import annotations

from dataclasses import dataclass

Coord = tuple[int, int]

OUTER_VOID_PADDING = 10


@dataclass(frozen=True, slots=True)
class BBox:
    """Inclusive topology bounding box (island or server-dense per frame)."""

    min_sx: int
    max_sx: int
    min_sy: int
    max_sy: int


def bbox_from_coords(coords: frozenset[Coord]) -> BBox:
    """Inclusive bbox over ``coords``; empty → ``BBox(0, 0, 0, 0)``."""

    if not coords:
        return BBox(0, 0, 0, 0)
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return BBox(min(xs), max(xs), min(ys), max(ys))


def expand_bbox(bb: BBox, padding: int) -> BBox:
    """Expand inclusive bbox by ``padding`` cells on each side."""

    return BBox(
        bb.min_sx - padding,
        bb.max_sx + padding,
        bb.min_sy - padding,
        bb.max_sy + padding,
    )


def cells_in_bbox(bb: BBox) -> frozenset[Coord]:
    """All integer grid coords inside inclusive ``bb``."""

    return frozenset(
        (sx, sy) for sx in range(bb.min_sx, bb.max_sx + 1) for sy in range(bb.min_sy, bb.max_sy + 1)
    )


def neighbors4(coord: Coord) -> tuple[Coord, Coord, Coord, Coord]:
    """Standard 4-neighbors on the active integer topology grid."""

    x, y = coord
    return ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))


def neighbors4_server(coord: Coord) -> tuple[Coord, Coord, Coord, Coord]:
    """Deprecated alias for :func:`neighbors4` (PR-F — prefer ``neighbors4``)."""

    return neighbors4(coord)


__all__ = [
    "BBox",
    "Coord",
    "OUTER_VOID_PADDING",
    "bbox_from_coords",
    "cells_in_bbox",
    "expand_bbox",
    "neighbors4",
    "neighbors4_server",
]
