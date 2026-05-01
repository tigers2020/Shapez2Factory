from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class QuadrantPosition(Enum):
    """Quadrant labels; layer string order is SW -> NW -> NE -> SE."""

    NE = "NE"
    SE = "SE"
    SW = "SW"
    NW = "NW"


_QUADRANT_ORDER = (
    QuadrantPosition.SW,
    QuadrantPosition.NW,
    QuadrantPosition.NE,
    QuadrantPosition.SE,
)


def quadrant_at_index(index: int) -> QuadrantPosition:
    return _QUADRANT_ORDER[index]


@dataclass(frozen=True, slots=True)
class NormalizedShapeCell:
    quadrant_index: int
    position: QuadrantPosition
    shape_code: str
    color_code: str
    shape_kind: str
    color_kind: str
    raw_token: str


@dataclass(frozen=True, slots=True)
class NormalizedShapeLayer:
    layer_index: int
    cells: tuple[NormalizedShapeCell, ...]


@dataclass(frozen=True, slots=True)
class NormalizedShapePattern:
    raw_code: str
    normalized_code: str
    layers: tuple[NormalizedShapeLayer, ...]
