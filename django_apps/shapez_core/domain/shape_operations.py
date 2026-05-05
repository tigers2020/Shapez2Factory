"""Pure shape transforms (rotate / cut / merge / swap halves).

These functions only permute or split ``ShapePart`` quadrants. Stacker gravity,
layer caps, painter, and color mixing live in ``shapez_solver`` application
services. See ``documents/game_rules/shape_encoding.md`` for SW→NW→NE→SE order.

Cut geometry: indices 0–1 are the **west** half (SW+NW), 2–3 the **east** half
(NE+SE). :func:`cut_vertical_halves` returns ``(west, east)``.
"""

from __future__ import annotations

from django_apps.shapez_core.domain.shape import EMPTY_PART, Shape, ShapeLayer, ShapePart


def rotate_cw(shape: Shape) -> Shape:
    return Shape(
        layers=tuple(
            ShapeLayer(
                quadrants=(
                    layer.quadrants[3],
                    layer.quadrants[0],
                    layer.quadrants[1],
                    layer.quadrants[2],
                )
            )
            for layer in shape.layers
        )
    ).strip_top_empty_layers()


def rotate_ccw(shape: Shape) -> Shape:
    return Shape(
        layers=tuple(
            ShapeLayer(
                quadrants=(
                    layer.quadrants[1],
                    layer.quadrants[2],
                    layer.quadrants[3],
                    layer.quadrants[0],
                )
            )
            for layer in shape.layers
        )
    ).strip_top_empty_layers()


def rotate_180(shape: Shape) -> Shape:
    return Shape(
        layers=tuple(
            ShapeLayer(
                quadrants=(
                    layer.quadrants[2],
                    layer.quadrants[3],
                    layer.quadrants[0],
                    layer.quadrants[1],
                )
            )
            for layer in shape.layers
        )
    ).strip_top_empty_layers()


def cut_vertical_halves(shape: Shape) -> tuple[Shape, Shape]:
    """Split each layer into west (``quadrants[0:2]``) and east (``[2:4]``) halves."""

    west = Shape(
        layers=tuple(
            ShapeLayer(
                quadrants=(
                    layer.quadrants[0],
                    layer.quadrants[1],
                    EMPTY_PART,
                    EMPTY_PART,
                )
            )
            for layer in shape.layers
        )
    ).strip_top_empty_layers()
    east = Shape(
        layers=tuple(
            ShapeLayer(
                quadrants=(
                    EMPTY_PART,
                    EMPTY_PART,
                    layer.quadrants[2],
                    layer.quadrants[3],
                )
            )
            for layer in shape.layers
        )
    ).strip_top_empty_layers()
    return west, east


def merge_disjoint_shape_layers(bottom: ShapeLayer, top: ShapeLayer) -> ShapeLayer | None:
    """If no quadrant has both inputs non-empty, merge into one layer; else ``None``."""

    quadrants: list[ShapePart] = []
    for bottom_part, top_part in zip(bottom.quadrants, top.quadrants, strict=True):
        if not bottom_part.is_empty and not top_part.is_empty:
            return None
        quadrants.append(bottom_part if not bottom_part.is_empty else top_part)
    return ShapeLayer(quadrants=(quadrants[0], quadrants[1], quadrants[2], quadrants[3]))


def swap_half_planes_single_layer(
    left: ShapeLayer, right: ShapeLayer
) -> tuple[ShapeLayer, ShapeLayer]:
    """Exchange east halves (NE+SE) between two single layers."""

    output_a = ShapeLayer(
        quadrants=(
            left.quadrants[0],
            left.quadrants[1],
            right.quadrants[2],
            right.quadrants[3],
        )
    )
    output_b = ShapeLayer(
        quadrants=(
            right.quadrants[0],
            right.quadrants[1],
            left.quadrants[2],
            left.quadrants[3],
        )
    )
    return output_a, output_b
