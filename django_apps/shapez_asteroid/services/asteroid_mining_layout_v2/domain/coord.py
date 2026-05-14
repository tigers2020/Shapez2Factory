"""
Integer grid coordinates and bounding boxes.

**Blueprint mapping (CANON):** decoded copy blueprints and STEP1
``mineable_placement_cells`` never include **X == 0** — that column index is not ingested
(see ``asteroid_reconstruction`` and ``blueprint_map_summary``). That is a **label /
ingestion convention**, not a physical “void column” between neighboring blueprint cells:
do not treat the missing ``x == 0`` key as extra empty space in the grid. Placement code
must not infer validity from ``x <= 0``; use ``mineable_placement_cells`` and barrier sets
instead.

``Coord.x`` must never be ``0`` at validated solver boundaries; this module only defines
types.
"""

from __future__ import annotations

from dataclasses import dataclass

type BlueprintCell = tuple[int, int]


@dataclass(frozen=True, slots=True)
class Coord:
    """Blueprint (X, Y) cell.

    Ingested blueprints omit **X == 0** (no such label); validated solver coords use
    ``x >= 1``. Missing ``x == 0`` is not an extra void between columns in the layout.
    """

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
