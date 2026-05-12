"""Canonical shape types for shapez2Solver.

One layer is eight characters (four two-character tokens). Token order and
``ShapeLayer.quadrants`` indices are SW, NW, NE, SE for indices 0..3.
See ``documents/game_rules/shape_encoding.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

QUADRANT_COUNT: Final[int] = 4


@dataclass(frozen=True, slots=True)
class ShapePart:
    kind: str
    color: str
    material: str = "solid"

    @property
    def is_empty(self) -> bool:
        """``--`` only; ``-r`` etc. are ink-only slots (fluid / shorthand), not geometric empty."""
        return self.kind == "-" and self.color == "-"

    @property
    def is_pin(self) -> bool:
        return self.kind == "P"

    @property
    def is_crystal(self) -> bool:
        return self.kind == "c"

    def with_color(self, color: str) -> ShapePart:
        if self.is_empty or self.is_pin:
            return self
        return ShapePart(kind=self.kind, color=color, material=self.material)


EMPTY_PART: Final[ShapePart] = ShapePart(kind="-", color="-", material="empty")
type ShapeQuadrants = tuple[ShapePart, ShapePart, ShapePart, ShapePart]


@dataclass(frozen=True, slots=True)
class ShapeLayer:
    """Four quadrants per layer: index order SW, NW, NE, SE."""

    quadrants: ShapeQuadrants

    def __post_init__(self) -> None:
        if len(self.quadrants) != QUADRANT_COUNT:
            raise ValueError("shape layers must contain exactly four quadrants")

    def is_empty(self) -> bool:
        return all(part.is_empty for part in self.quadrants)


@dataclass(frozen=True, slots=True)
class Shape:
    layers: tuple[ShapeLayer, ...]

    def __post_init__(self) -> None:
        if not self.layers:
            raise ValueError("shapes must contain at least one layer")

    @property
    def canonical_code(self) -> str:
        return ":".join(
            "".join(f"{part.kind}{part.color}" for part in layer.quadrants) for layer in self.layers
        )

    def non_empty_parts(self) -> tuple[ShapePart, ...]:
        return tuple(part for layer in self.layers for part in layer.quadrants if not part.is_empty)

    def is_single_layer(self) -> bool:
        return len(self.layers) == 1

    def has_unsupported_materials(self) -> bool:
        return any(part.is_pin or part.is_crystal for part in self.non_empty_parts())

    def strip_top_empty_layers(self) -> Shape:
        layers = list(self.layers)
        while len(layers) > 1 and layers[-1].is_empty():
            layers.pop()
        return Shape(layers=tuple(layers))


def empty_layer() -> ShapeLayer:
    return ShapeLayer(quadrants=(EMPTY_PART, EMPTY_PART, EMPTY_PART, EMPTY_PART))


def make_shape_layer(
    parts: tuple[ShapePart | None, ShapePart | None, ShapePart | None, ShapePart | None],
) -> ShapeLayer:
    return ShapeLayer(
        quadrants=(
            parts[0] or EMPTY_PART,
            parts[1] or EMPTY_PART,
            parts[2] or EMPTY_PART,
            parts[3] or EMPTY_PART,
        )
    )
