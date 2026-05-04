from __future__ import annotations

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.operation_engine import OperationEngine


def parse_shape(shape_code: str) -> Shape:
    """Shape code 문자열을 canonical Shape로 변환한다."""

    return shape_from_pattern(parse_shape_code_list(shape_code)[0])


def is_single_layer_shape_code(shape_code: str) -> bool:
    """Swapper 등 single-layer 전제 연산에서 사용한다."""

    return len(parse_shape(shape_code).layers) == 1


def rotate(shape_code: str, operation: OperationType) -> tuple[str, ...]:
    """회전 primitive의 canonical output code를 반환한다."""

    engine = OperationEngine()
    shape = parse_shape(shape_code)
    return tuple(output.canonical_code for output in engine.apply(operation, (shape,)))


def cut(shape_code: str) -> tuple[str, str]:
    """Cutter primitive의 left/right output code를 반환한다."""

    engine = OperationEngine()
    left_output, right_output = engine.cut(parse_shape(shape_code))
    return left_output.canonical_code, right_output.canonical_code


def swap(left_shape_code: str, right_shape_code: str) -> tuple[str, str]:
    """Swapper primitive의 2-output code를 engine semantics 기준으로 반환한다."""

    engine = OperationEngine()
    output_a, output_b = engine.swapper(
        parse_shape(left_shape_code), parse_shape(right_shape_code)
    )
    return output_a.canonical_code, output_b.canonical_code


def stack(bottom_shape_code: str, top_shape_code: str) -> tuple[str, ...]:
    """Stacker primitive의 output code를 반환한다."""

    engine = OperationEngine()
    return (
        engine.stacker(
            parse_shape(bottom_shape_code), parse_shape(top_shape_code)
        ).canonical_code,
    )


def apply_operation(
    operation: OperationType,
    inputs: tuple[str, ...],
) -> tuple[str, ...]:
    """Search action generator가 사용할 operation dispatch."""

    if operation in {OperationType.ROTATE_CW, OperationType.ROTATE_CCW, OperationType.ROTATE_180}:
        return rotate(inputs[0], operation)
    if operation == OperationType.CUTTER:
        return cut(inputs[0])
    if operation == OperationType.SWAPPER:
        return swap(inputs[0], inputs[1])
    if operation == OperationType.STACKER:
        return stack(inputs[0], inputs[1])
    raise ValueError(f"unsupported inventory search operation: {operation}")
