"""OperationEngine.apply 에 대응하는 순수 연산 헬퍼(유체는 fluid_semantics).

회전·절단·크리스탈 등은 여기서 한 번 정의하고 OperationEngine이 위임한다.
"""

from __future__ import annotations

from django_apps.shapez_core.domain.crystal_geometry import crystal_fill_gaps_and_pins
from django_apps.shapez_core.domain.shape import Shape, ShapeLayer, ShapePart
from django_apps.shapez_core.domain.shape_operations import (
    cut_vertical_halves,
    merge_disjoint_shape_layers,
    rotate_180,
    rotate_ccw,
    rotate_cw,
    swap_half_planes_single_layer,
)
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.color_mix_semantics import mix_color_pair
from django_apps.shapez_solver.services.fluid_semantics import (
    pure_fluid_color,
    uniform_fluid_output_from_template,
)
from django_apps.shapez_solver.services.shape_layer_physics import post_stack_physics


def rotate_shape(shape: Shape, operation_type: OperationType) -> Shape:
    if operation_type == OperationType.ROTATE_CW:
        return rotate_cw(shape)
    if operation_type == OperationType.ROTATE_CCW:
        return rotate_ccw(shape)
    if operation_type == OperationType.ROTATE_180:
        return rotate_180(shape)
    raise ValueError(f"not a rotate operation: {operation_type}")


def cutter_halves(shape: Shape) -> tuple[Shape, Shape]:
    """West half then east half (project quadrant order)."""

    return cut_vertical_halves(shape)


def half_destroyer_shape(shape: Shape) -> Shape:
    west, _east = cutter_halves(shape)
    return west


def splitter_outputs(shape: Shape) -> tuple[Shape, Shape]:
    return (shape, shape)


def swapper_outputs(left_shape: Shape, right_shape: Shape) -> tuple[Shape, Shape]:
    if len(left_shape.layers) != 1 or len(right_shape.layers) != 1:
        raise ValueError("swapper MVP supports only single-layer shapes")
    output_a_layer, output_b_layer = swap_half_planes_single_layer(
        left_shape.layers[0],
        right_shape.layers[0],
    )
    return Shape(layers=(output_a_layer,)), Shape(layers=(output_b_layer,))


def stacker_output(bottom: Shape, top: Shape) -> Shape:
    if len(bottom.layers) == 1 and len(top.layers) == 1:
        merged = merge_disjoint_shape_layers(bottom.layers[0], top.layers[0])
        if merged is not None:
            return Shape(layers=(merged,)).strip_top_empty_layers()
    combined = Shape(layers=(*bottom.layers, *top.layers))
    return post_stack_physics(combined)


def pin_pusher_output(shape: Shape) -> Shape:
    pin_bottom = ShapeLayer(
        quadrants=(
            ShapePart(kind="P", color="-", material="pin"),
            ShapePart(kind="P", color="-", material="pin"),
            ShapePart(kind="P", color="-", material="pin"),
            ShapePart(kind="P", color="-", material="pin"),
        )
    )
    combined = Shape(layers=(pin_bottom, *shape.layers))
    return post_stack_physics(combined)


def painter_output(shape: Shape, color: str) -> Shape:
    return Shape(
        layers=tuple(
            ShapeLayer(
                quadrants=(
                    layer.quadrants[0].with_color(color),
                    layer.quadrants[1].with_color(color),
                    layer.quadrants[2].with_color(color),
                    layer.quadrants[3].with_color(color),
                )
            )
            for layer in shape.layers
        )
    ).strip_top_empty_layers()


def painter_with_fluid_target(target_shape: Shape, fluid_shape: Shape) -> Shape:
    paint = pure_fluid_color(fluid_shape)
    return painter_output(target_shape, paint)


def color_mixer_fluids(left: Shape, right: Shape) -> Shape:
    lc = pure_fluid_color(left)
    rc = pure_fluid_color(right)
    mixed = mix_color_pair(lc, rc)
    return uniform_fluid_output_from_template(left, mixed)


def crystal_generator_output(shape: Shape, color: str) -> Shape:
    return crystal_fill_gaps_and_pins(shape, color)


__all__ = [
    "color_mixer_fluids",
    "crystal_generator_output",
    "cutter_halves",
    "half_destroyer_shape",
    "painter_output",
    "painter_with_fluid_target",
    "pin_pusher_output",
    "rotate_shape",
    "splitter_outputs",
    "stacker_output",
    "swapper_outputs",
]
