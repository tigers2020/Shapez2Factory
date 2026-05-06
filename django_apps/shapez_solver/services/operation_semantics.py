from __future__ import annotations

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.fluid_semantics import pure_fluid_color
from django_apps.shapez_solver.services.operation_engine import OperationEngine

_OPERATION_ENGINE = OperationEngine()

_ROTATE_OPS = frozenset(
    {
        OperationType.ROTATE_CW,
        OperationType.ROTATE_CCW,
        OperationType.ROTATE_180,
    }
)
_SINGLE_INPUT_ENGINE_OPS = frozenset(
    {
        OperationType.HALF_DESTROYER,
        OperationType.SPLITTER,
        OperationType.PIN_PUSHER,
    }
)


def parse_shape(shape_code: str, *, cache: dict[str, Shape] | None = None) -> Shape:
    """Shape code 문자열을 canonical Shape로 변환한다."""

    if cache is not None:
        hit = cache.get(shape_code)
        if hit is not None:
            return hit
    shape = shape_from_pattern(parse_shape_code_list(shape_code)[0])
    if cache is not None:
        cache[shape_code] = shape
    return shape


def is_single_layer_shape_code(shape_code: str) -> bool:
    """Swapper 등 single-layer 전제 연산에서 사용한다."""

    return len(parse_shape(shape_code).layers) == 1


def rotate(
    shape_code: str,
    operation: OperationType,
    *,
    shape_parse_cache: dict[str, Shape] | None = None,
) -> tuple[str, ...]:
    """회전 primitive의 canonical output code를 반환한다."""

    shape = parse_shape(shape_code, cache=shape_parse_cache)
    return tuple(output.canonical_code for output in _OPERATION_ENGINE.apply(operation, (shape,)))


def cut(shape_code: str, *, shape_parse_cache: dict[str, Shape] | None = None) -> tuple[str, str]:
    """Cutter primitive의 left/right output code를 반환한다."""

    left_output, right_output = _OPERATION_ENGINE.cut(
        parse_shape(shape_code, cache=shape_parse_cache),
    )
    return left_output.canonical_code, right_output.canonical_code


def swap(
    left_shape_code: str,
    right_shape_code: str,
    *,
    shape_parse_cache: dict[str, Shape] | None = None,
) -> tuple[str, str]:
    """Swapper primitive의 2-output code를 engine semantics 기준으로 반환한다."""

    output_a, output_b = _OPERATION_ENGINE.swapper(
        parse_shape(left_shape_code, cache=shape_parse_cache),
        parse_shape(right_shape_code, cache=shape_parse_cache),
    )
    return output_a.canonical_code, output_b.canonical_code


def stack(
    bottom_shape_code: str,
    top_shape_code: str,
    *,
    shape_parse_cache: dict[str, Shape] | None = None,
) -> tuple[str, ...]:
    """Stacker primitive의 output code를 반환한다."""

    return (
        _OPERATION_ENGINE.stacker(
            parse_shape(bottom_shape_code, cache=shape_parse_cache),
            parse_shape(top_shape_code, cache=shape_parse_cache),
        ).canonical_code,
    )


def merge_flow(
    left_shape_code: str,
    right_shape_code: str,
    *,
    shape_parse_cache: dict[str, Shape] | None = None,
) -> tuple[str, ...]:
    cache = shape_parse_cache
    out = _OPERATION_ENGINE.apply(
        OperationType.MERGE,
        (
            parse_shape(left_shape_code, cache=cache),
            parse_shape(right_shape_code, cache=cache),
        ),
    )
    return tuple(s.canonical_code for s in out)


def infer_uniform_shape_color(
    shape_code: str,
    *,
    shape_parse_cache: dict[str, Shape] | None = None,
) -> str | None:
    """모든 비어있지 않은·비-pin 칸의 색이 동일할 때 그 한 글자 색 코드. 유체 색 추론용."""

    shape = parse_shape(shape_code, cache=shape_parse_cache)
    colors: list[str] = []
    for layer in shape.layers:
        for part in layer.quadrants:
            if part.is_empty or part.is_pin:
                continue
            colors.append(part.color)
    if not colors:
        return None
    first = colors[0]
    if any(c != first for c in colors):
        return None
    return first


def _engine_outputs_single_input(
    operation: OperationType,
    shape_code: str,
    *,
    shape_parse_cache: dict[str, Shape] | None,
) -> tuple[str, ...]:
    return tuple(
        output.canonical_code
        for output in _OPERATION_ENGINE.apply(
            operation,
            (parse_shape(shape_code, cache=shape_parse_cache),),
        )
    )


def _apply_color_mixer(
    inputs: tuple[str, ...],
    *,
    shape_parse_cache: dict[str, Shape] | None,
) -> tuple[str, ...]:
    cache = shape_parse_cache
    left = parse_shape(inputs[0], cache=cache)
    right = parse_shape(inputs[1], cache=cache)
    try:
        pure_fluid_color(left)
        pure_fluid_color(right)
    except ValueError as exc:
        raise ValueError(f"color_mixer inputs must be pure color fluids: {exc}") from exc
    mixed = _OPERATION_ENGINE.apply(OperationType.COLOR_MIXER, (left, right))
    return tuple(output.canonical_code for output in mixed)


def _apply_painter(
    inputs: tuple[str, ...],
    paint_color: str | None,
    *,
    shape_parse_cache: dict[str, Shape] | None,
) -> tuple[str, ...]:
    cache = shape_parse_cache
    if len(inputs) == 2:
        # Graph edge order: slot "1" (`in-1`) before bare `in` → (fluid, target).
        fluid_code, target_code = inputs[0], inputs[1]
        fluid_shape = parse_shape(fluid_code, cache=cache)
        target_shape = parse_shape(target_code, cache=cache)
        return tuple(
            output.canonical_code
            for output in _OPERATION_ENGINE.apply(
                OperationType.PAINTER,
                (target_shape, fluid_shape),
            )
        )
    if paint_color is None:
        raise ValueError("painter requires paint_color or two inputs (fluid wire + shape)")
    ink = str(paint_color).strip()
    if len(ink) != 1:
        raise ValueError("paint_color must be a single character")
    return tuple(
        output.canonical_code
        for output in _OPERATION_ENGINE.apply(
            OperationType.PAINTER,
            (parse_shape(inputs[0], cache=cache),),
            color=ink,
        )
    )


def _apply_crystal_generator(
    inputs: tuple[str, ...],
    crystal_color: str | None,
    *,
    shape_parse_cache: dict[str, Shape] | None,
) -> tuple[str, ...]:
    cache = shape_parse_cache
    color: str | None = None
    if crystal_color is not None and str(crystal_color).strip():
        color = str(crystal_color).strip()
        if len(color) != 1:
            raise ValueError("crystal_color must be a single character")
    elif len(inputs) == 2:
        # Graph edge order: slot "1" (`in-1`) before bare `in` → (fluid, target).
        fluid_code, target_code = inputs[0], inputs[1]
        color = pure_fluid_color(parse_shape(fluid_code, cache=cache))
        target_shape = parse_shape(target_code, cache=cache)
        return tuple(
            output.canonical_code
            for output in _OPERATION_ENGINE.apply(
                OperationType.CRYSTAL_GENERATOR,
                (target_shape,),
                color=color,
            )
        )
    if color is None:
        raise ValueError(
            "crystal_generator requires crystal_color or two inputs (fluid wire + shape)",
        )
    return tuple(
        output.canonical_code
        for output in _OPERATION_ENGINE.apply(
            OperationType.CRYSTAL_GENERATOR,
            (parse_shape(inputs[0], cache=cache),),
            color=color,
        )
    )


def apply_operation(
    operation: OperationType,
    inputs: tuple[str, ...],
    *,
    paint_color: str | None = None,
    crystal_color: str | None = None,
    shape_parse_cache: dict[str, Shape] | None = None,
) -> tuple[str, ...]:
    """Search action generator가 사용할 operation dispatch."""

    cache = shape_parse_cache
    if operation in _ROTATE_OPS:
        return rotate(inputs[0], operation, shape_parse_cache=cache)
    if operation == OperationType.CUTTER:
        return cut(inputs[0], shape_parse_cache=cache)
    if operation in _SINGLE_INPUT_ENGINE_OPS:
        return _engine_outputs_single_input(operation, inputs[0], shape_parse_cache=cache)
    if operation == OperationType.SWAPPER:
        return swap(inputs[0], inputs[1], shape_parse_cache=cache)
    if operation == OperationType.STACKER:
        return stack(inputs[0], inputs[1], shape_parse_cache=cache)
    if operation == OperationType.MERGE:
        return merge_flow(inputs[0], inputs[1], shape_parse_cache=cache)
    if operation == OperationType.COLOR_MIXER:
        return _apply_color_mixer(inputs, shape_parse_cache=cache)
    if operation == OperationType.PAINTER:
        return _apply_painter(inputs, paint_color, shape_parse_cache=cache)
    if operation == OperationType.CRYSTAL_GENERATOR:
        return _apply_crystal_generator(inputs, crystal_color, shape_parse_cache=cache)
    raise ValueError(f"unsupported inventory search operation: {operation}")
