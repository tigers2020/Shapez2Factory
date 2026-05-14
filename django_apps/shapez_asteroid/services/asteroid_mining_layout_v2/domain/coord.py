"""
Integer grid coordinates and bounding boxes.

Project convention (blueprint grid): ``Coord.x`` must never be ``0``; see
``documents/research`` and architecture rules. v2 enforces that at validation time;
this module only defines types.
"""

from __future__ import annotations

from dataclasses import dataclass

# Blueprint (X, Y) integer pair; x == 0 is illegal at solver boundaries (asserted later).
type Coord = tuple[int, int]


@dataclass(frozen=True, slots=True)
class BBox:
    """Axis-aligned bounding box in blueprint cell coordinates."""

    min_x: int
    min_y: int
    max_x: int
    max_y: int
