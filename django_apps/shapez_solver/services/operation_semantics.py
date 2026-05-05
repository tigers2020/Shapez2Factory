from __future__ import annotations

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.operation_engine import OperationEngine

_OPERATION_ENGINE = OperationEngine()


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


def apply_operation(
    operation: OperationType,
    inputs: tuple[str, ...],
    *,
    paint_color: str | None = None,
    shape_parse_cache: dict[str, Shape] | None = None,
) -> tuple[str, ...]:
    """Search action generator가 사용할 operation dispatch."""

    cache = shape_parse_cache
    if operation in {OperationType.ROTATE_CW, OperationType.ROTATE_CCW, OperationType.ROTATE_180}:
        return rotate(inputs[0], operation, shape_parse_cache=cache)
    if operation == OperationType.CUTTER:
        return cut(inputs[0], shape_parse_cache=cache)
    if operation == OperationType.HALF_DESTROYER:
        return tuple(
            output.canonical_code
            for output in _OPERATION_ENGINE.apply(
                OperationType.HALF_DESTROYER,
                (parse_shape(inputs[0], cache=cache),),
            )
        )
    if operation == OperationType.SPLITTER:
        return tuple(
            output.canonical_code
            for output in _OPERATION_ENGINE.apply(
                OperationType.SPLITTER,
                (parse_shape(inputs[0], cache=cache),),
            )
        )
    if operation == OperationType.PIN_PUSHER:
        return tuple(
            output.canonical_code
            for output in _OPERATION_ENGINE.apply(
                OperationType.PIN_PUSHER,
                (parse_shape(inputs[0], cache=cache),),
            )
        )
    if operation == OperationType.SWAPPER:
        return swap(inputs[0], inputs[1], shape_parse_cache=cache)
    if operation == OperationType.STACKER:
        return stack(inputs[0], inputs[1], shape_parse_cache=cache)
    if operation == OperationType.COLOR_MIXER:
        shapes = (
            parse_shape(inputs[0], cache=cache),
            parse_shape(inputs[1], cache=cache),
        )
        mixed = _OPERATION_ENGINE.apply(OperationType.COLOR_MIXER, shapes)
        return tuple(output.canonical_code for output in mixed)
    if operation == OperationType.PAINTER:
        if paint_color is None:
            raise ValueError("painter requires paint_color")
        color = str(paint_color).strip()
        if len(color) != 1:
            raise ValueError("paint_color must be a single character")
        return tuple(
            output.canonical_code
            for output in _OPERATION_ENGINE.apply(
                OperationType.PAINTER,
                (parse_shape(inputs[0], cache=cache),),
                color=color,
            )
        )
    raise ValueError(f"unsupported inventory search operation: {operation}")
