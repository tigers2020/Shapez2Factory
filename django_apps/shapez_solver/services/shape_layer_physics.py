"""Stack / column gravity applied after stacker and pin pusher (solver-side model)."""

from __future__ import annotations

from typing import Final

from django_apps.shapez_core.domain.shape import EMPTY_PART, Shape, ShapeLayer, ShapePart

# 일반 모드 레이어 상한. Insane(5레이어)는 향후 설정/SolveContext로 확장.
MAX_SHAPE_LAYERS: Final[int] = 4
_MAX_GRAVITY_ITERATIONS: Final[int] = 32


def apply_column_gravity_once(shape: Shape) -> Shape:
    """Per-quadrant stable compaction: non-empty parts sink within their column."""

    layers = shape.layers
    n = len(layers)
    if n <= 1:
        return shape
    new_quads_per_layer: list[list[ShapePart]] = [[] for _ in range(n)]
    for q in range(4):
        col = [layers[i].quadrants[q] for i in range(n)]
        non_empty = [p for p in col if not p.is_empty]
        new_col = non_empty + [EMPTY_PART] * (n - len(non_empty))
        for i in range(n):
            new_quads_per_layer[i].append(new_col[i])
    return Shape(
        layers=tuple(
            ShapeLayer(
                quadrants=(
                    new_quads_per_layer[i][0],
                    new_quads_per_layer[i][1],
                    new_quads_per_layer[i][2],
                    new_quads_per_layer[i][3],
                )
            )
            for i in range(n)
        )
    )


def gravity_fixpoint(shape: Shape) -> Shape:
    current = shape
    for _ in range(_MAX_GRAVITY_ITERATIONS):
        nxt = apply_column_gravity_once(current)
        if nxt.canonical_code == current.canonical_code:
            return nxt
        current = nxt
    return current


def enforce_max_layers(shape: Shape, max_layers: int) -> Shape:
    layer_list = list(shape.layers)
    while len(layer_list) > max_layers:
        layer_list.pop()
    return Shape(layers=tuple(layer_list))


def post_stack_physics(shape: Shape) -> Shape:
    settled = gravity_fixpoint(shape)
    capped = enforce_max_layers(settled, MAX_SHAPE_LAYERS)
    return gravity_fixpoint(capped).strip_top_empty_layers()


__all__ = [
    "MAX_SHAPE_LAYERS",
    "apply_column_gravity_once",
    "enforce_max_layers",
    "gravity_fixpoint",
    "post_stack_physics",
]
