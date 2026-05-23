"""Ring / spine option enumeration for RTTP skeleton (boundary-offset frame)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.snapshots.grid_contract import BBox, bbox_from_coords


class RingVariant(StrEnum):
    FULL_RING = "full_ring"
    C_SPINE = "c_spine"
    ONE_SIDE_SPINE = "one_side_spine"


@dataclass(frozen=True, slots=True)
class RingOption:
    variant: RingVariant
    ring_cells: frozenset[Coord]


def boundary_offset_frame(mineable_cells: frozenset[Coord]) -> frozenset[Coord]:
    """Cells one step outside the inclusive mineable bbox (ring frame)."""

    if not mineable_cells:
        return frozenset()
    bbox = bbox_from_coords(mineable_cells)
    return _frame_from_bbox(bbox)


def build_ring_options(mineable_cells: frozenset[Coord]) -> tuple[RingOption, ...]:
    """Evaluate full ring, C-spine, and one-side spine on the boundary-offset frame."""

    if not mineable_cells:
        return (
            RingOption(RingVariant.FULL_RING, frozenset()),
            RingOption(RingVariant.C_SPINE, frozenset()),
            RingOption(RingVariant.ONE_SIDE_SPINE, frozenset()),
        )

    bbox = bbox_from_coords(mineable_cells)
    frame = _frame_from_bbox(bbox)
    usable = frozenset(cell for cell in frame if cell not in mineable_cells)

    top = frozenset((sx, bbox.min_sy - 1) for sx in range(bbox.min_sx - 1, bbox.max_sx + 2))
    left = frozenset((bbox.min_sx - 1, sy) for sy in range(bbox.min_sy, bbox.max_sy + 1))
    right = frozenset((bbox.max_sx + 1, sy) for sy in range(bbox.min_sy, bbox.max_sy + 1))

    full_ring = usable
    one_side_spine = usable & top
    # C-spine: three sides (top + left + right), bottom open.
    c_spine = usable & (top | left | right)

    return (
        RingOption(RingVariant.FULL_RING, full_ring),
        RingOption(RingVariant.C_SPINE, c_spine),
        RingOption(RingVariant.ONE_SIDE_SPINE, one_side_spine),
    )


def _frame_from_bbox(bbox: BBox) -> frozenset[Coord]:
    cells: set[Coord] = set()
    for sx in range(bbox.min_sx - 1, bbox.max_sx + 2):
        cells.add((sx, bbox.min_sy - 1))
        cells.add((sx, bbox.max_sy + 1))
    for sy in range(bbox.min_sy, bbox.max_sy + 1):
        cells.add((bbox.min_sx - 1, sy))
        cells.add((bbox.max_sx + 1, sy))
    return frozenset(cells)


__all__ = [
    "RingOption",
    "RingVariant",
    "boundary_offset_frame",
    "build_ring_options",
]
