"""Convert ``NormalizedShapePattern`` and :class:`~django_apps.shapez_core.domain.shape.Shape`.

Canonical encoding: layer tokens SW, NW, NE, SE (``shape_encoding.md``).
"""

from __future__ import annotations

from django_apps.shapez_core.domain.shape import EMPTY_PART, Shape, ShapeLayer, ShapePart
from django_apps.shapez_core.domain.shape_pattern import (
    NormalizedShapeCell,
    NormalizedShapeLayer,
    NormalizedShapePattern,
    quadrant_at_index,
)


def shape_from_pattern(pattern: NormalizedShapePattern) -> Shape:
    return Shape(
        layers=tuple(
            ShapeLayer(
                quadrants=(
                    _part_from_cell(layer.cells[0]),
                    _part_from_cell(layer.cells[1]),
                    _part_from_cell(layer.cells[2]),
                    _part_from_cell(layer.cells[3]),
                )
            )
            for layer in pattern.layers
        )
    ).strip_top_empty_layers()


def pattern_from_shape(shape: Shape) -> NormalizedShapePattern:
    layers = tuple(
        NormalizedShapeLayer(
            layer_index=layer_index,
            cells=tuple(
                _cell_from_part(quadrant_index, part)
                for quadrant_index, part in enumerate(layer.quadrants)
            ),
        )
        for layer_index, layer in enumerate(shape.layers)
    )
    return NormalizedShapePattern(
        raw_code=shape.canonical_code,
        normalized_code=shape.canonical_code,
        layers=layers,
    )


def normalize_shape(shape: Shape) -> Shape:
    normalized_layers = tuple(
        ShapeLayer(
            quadrants=(
                _normalize_part(layer.quadrants[0]),
                _normalize_part(layer.quadrants[1]),
                _normalize_part(layer.quadrants[2]),
                _normalize_part(layer.quadrants[3]),
            )
        )
        for layer in shape.layers
    )
    return Shape(layers=normalized_layers).strip_top_empty_layers()


def _part_from_cell(cell: NormalizedShapeCell) -> ShapePart:
    if cell.shape_code == "-":
        if cell.color_code == "-":
            return EMPTY_PART
        return ShapePart(kind="-", color=cell.color_code, material="fluid_ink")
    material = "solid"
    if cell.shape_code == "P":
        material = "pin"
    elif cell.shape_code == "c":
        material = "crystal"
    elif cell.shape_code == "t":
        material = "fluid_tank"
    return ShapePart(kind=cell.shape_code, color=cell.color_code, material=material)


def _cell_from_part(quadrant_index: int, part: ShapePart) -> NormalizedShapeCell:
    return NormalizedShapeCell(
        quadrant_index=quadrant_index,
        position=quadrant_at_index(quadrant_index),
        shape_code=part.kind,
        color_code=part.color,
        shape_kind=_shape_kind(part),
        color_kind=_color_kind(part),
        raw_token=f"{part.kind}{part.color}",
    )


def _normalize_part(part: ShapePart) -> ShapePart:
    if part.is_empty:
        return EMPTY_PART
    return ShapePart(part.kind, part.color, part.material)


def _shape_kind(part: ShapePart) -> str:
    if part.kind == "-":
        return "empty"
    if part.kind == "P":
        return "pin"
    if part.kind == "c":
        return "crystal"
    if part.kind == "t":
        return "fluid_tank"
    return {
        "C": "circle",
        "R": "rectangle",
        "S": "spike",
        "W": "diamond",
    }.get(part.kind, "unknown")


def _color_kind(part: ShapePart) -> str:
    if part.kind == "P" and part.color == "-":
        return "uncolored"
    return {
        "-": "empty",
        "u": "uncolored",
        "r": "red",
        "g": "green",
        "b": "blue",
        "c": "cyan",
        "m": "magenta",
        "y": "yellow",
        "w": "white",
    }.get(part.color, "unknown")
