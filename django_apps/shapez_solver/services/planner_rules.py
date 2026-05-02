from __future__ import annotations

from collections.abc import Callable

from django_apps.shapez_core.domain.shape import Shape, ShapeLayer, ShapePart
from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.recipe import (
    RecipeCost,
    RecipeRef,
    SolveContext,
    SolvedRecipe,
    SourceRecipe,
)
from django_apps.shapez_solver.services.operation_engine import OperationEngine
from django_apps.shapez_solver.services.planner_support import (
    build_operation_solution,
    is_empty_shape,
    is_uncolored_full_source,
    is_uncolored_single_kind,
    paint_shape,
    single_quadrant_shapes,
    split_halves,
    uniform_non_empty_color,
)

SolveShapeFn = Callable[[Shape, SolveContext], SolvedRecipe]


def try_source(target: Shape, ctx: SolveContext) -> SolvedRecipe | None:
    if not is_uncolored_full_source(target):
        return None
    source = SourceRecipe(id=ctx.allocate_id("source"), shape=target, label="Source")
    ref = RecipeRef(recipe_id=source.id, output_index=0, shape=target)
    return SolvedRecipe(
        ref=ref,
        recipes=(source,),
        cost=RecipeCost(
            operations=0,
            sources=1,
            depth=1,
            reused_nodes=0,
        ),
    )


def try_rotation(
    target: Shape,
    ctx: SolveContext,
    *,
    solve_shape: SolveShapeFn,
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    rotations = (
        (OperationType.ROTATE_CW, operation_engine.rotate_ccw(target)),
        (OperationType.ROTATE_CCW, operation_engine.rotate_cw(target)),
        (OperationType.ROTATE_180, operation_engine.rotate_180(target)),
    )
    candidates: list[SolvedRecipe] = []
    target_key = target.canonical_code
    for operation_type, base_shape in rotations:
        if base_shape.canonical_code >= target_key:
            continue
        base = solve_shape(base_shape, ctx)
        candidates.append(
            build_operation_solution(
                ctx,
                operation_type=operation_type,
                inputs=(base.ref,),
                outputs=operation_engine.apply(operation_type, (base.ref.shape,)),
                selected_output_index=0,
                label=OPERATION_CATALOG[operation_type].label,
                description=OPERATION_CATALOG[operation_type].description,
                dependencies=(base,),
            )
        )
    return min(candidates, key=lambda item: item.cost.as_sort_key()) if candidates else None


def try_stack_layers(
    target: Shape,
    ctx: SolveContext,
    *,
    solve_shape: SolveShapeFn,
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    if len(target.layers) <= 1:
        return None
    current = solve_shape(Shape(layers=(target.layers[0],)), ctx)
    for next_layer in target.layers[1:]:
        top = solve_shape(Shape(layers=(next_layer,)), ctx)
        current = build_operation_solution(
            ctx,
            operation_type=OperationType.STACKER,
            inputs=(current.ref, top.ref),
            outputs=operation_engine.apply(
                OperationType.STACKER,
                (current.ref.shape, top.ref.shape),
            ),
            selected_output_index=0,
            label=OPERATION_CATALOG[OperationType.STACKER].label,
            description=OPERATION_CATALOG[OperationType.STACKER].description,
            dependencies=(current, top),
        )
    return current


def try_paint(
    target: Shape,
    ctx: SolveContext,
    *,
    solve_shape: SolveShapeFn,
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    color = uniform_non_empty_color(target)
    if color is None:
        return None
    skeleton = paint_shape(target, "u")
    if skeleton.canonical_code == target.canonical_code:
        return None
    base = solve_shape(skeleton, ctx)
    return build_operation_solution(
        ctx,
        operation_type=OperationType.PAINTER,
        inputs=(base.ref,),
        outputs=operation_engine.apply(OperationType.PAINTER, (base.ref.shape,), color=color),
        selected_output_index=0,
        label=f"{OPERATION_CATALOG[OperationType.PAINTER].label} ({color})",
        description=f"Paint the shape {color}.",
        dependencies=(base,),
        color=color,
    )


def try_assemble_halves(
    target: Shape,
    ctx: SolveContext,
    *,
    solve_shape: SolveShapeFn,
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    if not target.is_single_layer():
        return None
    left_half, right_half = split_halves(target)
    if is_empty_shape(left_half) or is_empty_shape(right_half):
        return None
    left = solve_shape(left_half, ctx)
    right = solve_shape(right_half, ctx)
    outputs = operation_engine.apply(OperationType.SWAPPER, (left.ref.shape, right.ref.shape))
    if outputs[0] != target:
        return None
    return build_operation_solution(
        ctx,
        operation_type=OperationType.SWAPPER,
        inputs=(left.ref, right.ref),
        outputs=outputs,
        selected_output_index=0,
        label=OPERATION_CATALOG[OperationType.SWAPPER].label,
        description=OPERATION_CATALOG[OperationType.SWAPPER].description,
        dependencies=(left, right),
    )


def try_assemble_quadrants(
    target: Shape,
    ctx: SolveContext,
    *,
    solve_shape: SolveShapeFn,
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    if not target.is_single_layer():
        return None
    quadrant_shapes = single_quadrant_shapes(target)
    if len(quadrant_shapes) <= 1:
        return None
    solved_parts = [solve_shape(shape, ctx) for shape in quadrant_shapes]
    current = solved_parts[0]
    for next_part in solved_parts[1:]:
        outputs = operation_engine.apply(
            OperationType.STACKER,
            (current.ref.shape, next_part.ref.shape),
        )
        current = build_operation_solution(
            ctx,
            operation_type=OperationType.STACKER,
            inputs=(current.ref, next_part.ref),
            outputs=outputs,
            selected_output_index=0,
            label=OPERATION_CATALOG[OperationType.STACKER].label,
            description="Merge disjoint quadrants into a buildable layer.",
            dependencies=(current, next_part),
        )
    return current if current.ref.shape == target else None


def try_cut_from_source(
    target: Shape,
    ctx: SolveContext,
    *,
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    if not target.is_single_layer() or not is_uncolored_single_kind(target):
        return None
    kind = next(part.kind for part in target.non_empty_parts())
    source_shape = Shape(
        layers=(
            ShapeLayer(
                quadrants=(
                    ShapePart(kind=kind, color="u"),
                    ShapePart(kind=kind, color="u"),
                    ShapePart(kind=kind, color="u"),
                    ShapePart(kind=kind, color="u"),
                )
            ),
        )
    )
    source = try_source(source_shape, ctx)
    if source is None:
        return None
    if source.ref.shape == target:
        return source

    queue: list[SolvedRecipe] = [source]
    visited = {source.ref.shape.canonical_code}
    for _depth in range(3):
        next_queue: list[SolvedRecipe] = []
        for recipe in queue:
            derived = [
                _derive_cut_output(ctx, recipe, 0, operation_engine),
                _derive_cut_output(ctx, recipe, 1, operation_engine),
                _derive_rotation(ctx, recipe, OperationType.ROTATE_CW, operation_engine),
                _derive_rotation(ctx, recipe, OperationType.ROTATE_CCW, operation_engine),
                _derive_rotation(ctx, recipe, OperationType.ROTATE_180, operation_engine),
            ]
            for candidate in derived:
                code = candidate.ref.shape.canonical_code
                if code in visited:
                    continue
                if candidate.ref.shape == target:
                    return candidate
                visited.add(code)
                next_queue.append(candidate)
        queue = next_queue
    return None


def _derive_cut_output(
    ctx: SolveContext,
    recipe: SolvedRecipe,
    output_index: int,
    operation_engine: OperationEngine,
) -> SolvedRecipe:
    outputs = operation_engine.apply(OperationType.CUTTER, (recipe.ref.shape,))
    return build_operation_solution(
        ctx,
        operation_type=OperationType.CUTTER,
        inputs=(recipe.ref,),
        outputs=outputs,
        selected_output_index=output_index,
        label=OPERATION_CATALOG[OperationType.CUTTER].label,
        description=OPERATION_CATALOG[OperationType.CUTTER].description,
        dependencies=(recipe,),
    )


def _derive_rotation(
    ctx: SolveContext,
    recipe: SolvedRecipe,
    operation_type: OperationType,
    operation_engine: OperationEngine,
) -> SolvedRecipe:
    outputs = operation_engine.apply(operation_type, (recipe.ref.shape,))
    return build_operation_solution(
        ctx,
        operation_type=operation_type,
        inputs=(recipe.ref,),
        outputs=outputs,
        selected_output_index=0,
        label=OPERATION_CATALOG[operation_type].label,
        description=OPERATION_CATALOG[operation_type].description,
        dependencies=(recipe,),
    )
