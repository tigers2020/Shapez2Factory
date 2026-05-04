from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from django_apps.shapez_core.domain.shape import EMPTY_PART, Shape, ShapeLayer, ShapePart
from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.recipe import SolveContext, SolvedRecipe
from django_apps.shapez_solver.services.operation_engine import OperationEngine
from django_apps.shapez_solver.services.planner_support import (
    build_binary_operation_solution_overlapping_deps,
    build_operation_solution,
)

type SolveShapeFn = Callable[[Shape, SolveContext], SolvedRecipe]
type ColorMatchMode = Literal["exact"]
type PatternTemplateId = Literal["half_swapper", "checker_swapper"]
type PatternTemplateBuildFn = Callable[
    [Shape, SolveContext, SolveShapeFn, OperationEngine],
    SolvedRecipe,
]
type Signature = tuple[int, int, int, int]

_HALF_SIGNATURE: Signature = (0, 0, 1, 1)
_CHECKER_SIGNATURE: Signature = (0, 1, 0, 1)


@dataclass(frozen=True, slots=True)
class PatternTemplateDefinition:
    template_id: PatternTemplateId
    input_ports: tuple[str, ...]
    output_ports: tuple[str, ...]
    build: PatternTemplateBuildFn


@dataclass(frozen=True, slots=True)
class PrebuiltPatternDefinition:
    family_id: str
    canonical_signature: Signature
    rotation_equivalent_signatures: tuple[Signature, ...]
    color_match_mode: ColorMatchMode
    template_id: PatternTemplateId


@dataclass(frozen=True, slots=True)
class PrebuiltPatternMatch:
    definition: PrebuiltPatternDefinition
    template: PatternTemplateDefinition
    canonical_target: Shape
    canonicalized_by_cw_steps: int


def _build_half_swapper_solution(
    target: Shape,
    ctx: SolveContext,
    solve_shape: SolveShapeFn,
    operation_engine: OperationEngine,
) -> SolvedRecipe:
    layer = target.layers[0]
    left_source = solve_shape(_full_shape_for_part(layer.quadrants[0]), ctx)
    right_source = solve_shape(_full_shape_for_part(layer.quadrants[2]), ctx)

    left_half = _build_unary_operation_solution(
        ctx,
        operation_type=OperationType.CUTTER,
        source=left_source,
        operation_engine=operation_engine,
        selected_output_index=0,
    )
    right_half = _build_unary_operation_solution(
        ctx,
        operation_type=OperationType.CUTTER,
        source=right_source,
        operation_engine=operation_engine,
        selected_output_index=1,
    )
    return _build_binary_operation_solution(
        ctx,
        operation_type=OperationType.SWAPPER,
        left=left_half,
        right=right_half,
        operation_engine=operation_engine,
    )


def _build_checker_swapper_solution(
    target: Shape,
    ctx: SolveContext,
    solve_shape: SolveShapeFn,
    operation_engine: OperationEngine,
) -> SolvedRecipe:
    layer = target.layers[0]
    left_half_target = Shape(
        layers=(
            ShapeLayer(
                quadrants=(
                    layer.quadrants[0],
                    layer.quadrants[1],
                    EMPTY_PART,
                    EMPTY_PART,
                )
            ),
        )
    )
    left_half = solve_shape(left_half_target, ctx)
    right_half = _build_unary_operation_solution(
        ctx,
        operation_type=OperationType.ROTATE_180,
        source=left_half,
        operation_engine=operation_engine,
    )
    return _build_binary_operation_solution(
        ctx,
        operation_type=OperationType.SWAPPER,
        left=left_half,
        right=right_half,
        operation_engine=operation_engine,
    )


PATTERN_TEMPLATE_REGISTRY: tuple[PatternTemplateDefinition, ...] = (
    PatternTemplateDefinition(
        template_id="half_swapper",
        input_ports=("leftSource", "rightSource"),
        output_ports=("targetShape",),
        build=_build_half_swapper_solution,
    ),
    PatternTemplateDefinition(
        template_id="checker_swapper",
        input_ports=("leftHalf",),
        output_ports=("targetShape",),
        build=_build_checker_swapper_solution,
    ),
)

PREBUILT_PATTERN_REGISTRY: tuple[PrebuiltPatternDefinition, ...] = (
    PrebuiltPatternDefinition(
        family_id="half_and_half",
        canonical_signature=_HALF_SIGNATURE,
        rotation_equivalent_signatures=(
            (0, 0, 1, 1),
            (0, 1, 1, 0),
            (1, 1, 0, 0),
            (1, 0, 0, 1),
        ),
        color_match_mode="exact",
        template_id="half_swapper",
    ),
    PrebuiltPatternDefinition(
        family_id="checker",
        canonical_signature=_CHECKER_SIGNATURE,
        rotation_equivalent_signatures=(_CHECKER_SIGNATURE,),
        color_match_mode="exact",
        template_id="checker_swapper",
    ),
)


def try_prebuilt_pattern(
    target: Shape,
    ctx: SolveContext,
    *,
    solve_shape: SolveShapeFn,
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    match = match_prebuilt_pattern(target, operation_engine=operation_engine)
    if match is None:
        return None

    solved = match.template.build(match.canonical_target, ctx, solve_shape, operation_engine)
    return _apply_restore_rotation(
        solved,
        match.canonicalized_by_cw_steps,
        ctx,
        operation_engine=operation_engine,
    )


def match_prebuilt_pattern(
    target: Shape,
    *,
    operation_engine: OperationEngine,
) -> PrebuiltPatternMatch | None:
    if not target.is_single_layer() or target.has_unsupported_materials():
        return None
    if len(target.non_empty_parts()) != 4:
        return None

    for definition in PREBUILT_PATTERN_REGISTRY:
        for cw_steps in range(4):
            rotated = _rotate_cw_steps(target, cw_steps, operation_engine)
            signature = _shape_signature(rotated)
            if signature is None:
                continue
            if signature not in definition.rotation_equivalent_signatures:
                continue
            if signature != definition.canonical_signature:
                continue
            return PrebuiltPatternMatch(
                definition=definition,
                template=_get_pattern_template(definition.template_id),
                canonical_target=rotated,
                canonicalized_by_cw_steps=cw_steps,
            )
    return None


def _get_pattern_template(template_id: PatternTemplateId) -> PatternTemplateDefinition:
    for template in PATTERN_TEMPLATE_REGISTRY:
        if template.template_id == template_id:
            return template
    raise ValueError(f"Unsupported prebuilt template: {template_id}")


def _apply_restore_rotation(
    solved: SolvedRecipe,
    canonicalized_by_cw_steps: int,
    ctx: SolveContext,
    *,
    operation_engine: OperationEngine,
) -> SolvedRecipe:
    operation_type = _restore_rotation_operation(canonicalized_by_cw_steps)
    if operation_type is None:
        return solved
    return _build_unary_operation_solution(
        ctx,
        operation_type=operation_type,
        source=solved,
        operation_engine=operation_engine,
    )


def _restore_rotation_operation(cw_steps: int) -> OperationType | None:
    restore_by_steps = {
        0: None,
        1: OperationType.ROTATE_CCW,
        2: OperationType.ROTATE_180,
        3: OperationType.ROTATE_CW,
    }
    return restore_by_steps[cw_steps]


def _shape_signature(shape: Shape) -> Signature | None:
    if not shape.is_single_layer():
        return None
    layer = shape.layers[0]
    if any(part.is_empty for part in layer.quadrants):
        return None

    mapping: dict[tuple[str, str, str], int] = {}
    next_index = 0
    signature: list[int] = []
    for part in layer.quadrants:
        key = (part.kind, part.color, part.material)
        if key not in mapping:
            mapping[key] = next_index
            next_index += 1
        signature.append(mapping[key])
    if len(mapping) != 2:
        return None
    return (signature[0], signature[1], signature[2], signature[3])


def _rotate_cw_steps(
    shape: Shape,
    cw_steps: int,
    operation_engine: OperationEngine,
) -> Shape:
    rotated = shape
    for _ in range(cw_steps):
        rotated = operation_engine.rotate_cw(rotated)
    return rotated


def _full_shape_for_part(part: ShapePart) -> Shape:
    return Shape(
        layers=(
            ShapeLayer(
                quadrants=(
                    part,
                    part,
                    part,
                    part,
                )
            ),
        )
    )


def _build_unary_operation_solution(
    ctx: SolveContext,
    *,
    operation_type: OperationType,
    source: SolvedRecipe,
    operation_engine: OperationEngine,
    selected_output_index: int = 0,
    label: str | None = None,
    description: str | None = None,
) -> SolvedRecipe:
    outputs = operation_engine.apply(operation_type, (source.ref.shape,))
    catalog_entry = OPERATION_CATALOG[operation_type]
    return build_operation_solution(
        ctx,
        operation_type=operation_type,
        inputs=(source.ref,),
        outputs=outputs,
        selected_output_index=selected_output_index,
        label=label or catalog_entry.label,
        description=description or catalog_entry.description,
        dependencies=(source,),
    )


def _build_binary_operation_solution(
    ctx: SolveContext,
    *,
    operation_type: OperationType,
    left: SolvedRecipe,
    right: SolvedRecipe,
    operation_engine: OperationEngine,
    selected_output_index: int = 0,
    label: str | None = None,
    description: str | None = None,
) -> SolvedRecipe:
    outputs = operation_engine.apply(
        operation_type,
        (left.ref.shape, right.ref.shape),
    )
    catalog_entry = OPERATION_CATALOG[operation_type]
    return build_binary_operation_solution_overlapping_deps(
        ctx,
        operation_type=operation_type,
        left=left,
        right=right,
        outputs=outputs,
        selected_output_index=selected_output_index,
        label=label or catalog_entry.label,
        description=description or catalog_entry.description,
    )
