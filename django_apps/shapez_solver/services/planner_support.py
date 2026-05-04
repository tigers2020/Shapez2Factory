from __future__ import annotations

from itertools import chain

from django_apps.shapez_core.domain.shape import EMPTY_PART, Shape, ShapeLayer, ShapePart
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.recipe import (
    OperationRecipe,
    RecipeCost,
    RecipeRef,
    SolveContext,
    SolvedRecipe,
    SourceRecipe,
)


def build_operation_solution(
    ctx: SolveContext,
    *,
    operation_type: OperationType,
    inputs: tuple[RecipeRef, ...],
    outputs: tuple[Shape, ...],
    selected_output_index: int,
    label: str,
    description: str,
    dependencies: tuple[SolvedRecipe, ...],
    color: str | None = None,
) -> SolvedRecipe:
    recipe = OperationRecipe(
        id=ctx.allocate_id("op"),
        operation_type=operation_type,
        inputs=inputs,
        outputs=outputs,
        label=label,
        description=description,
        color=color,
    )
    ref = RecipeRef(
        recipe_id=recipe.id,
        output_index=selected_output_index,
        shape=outputs[selected_output_index],
    )
    combined = tuple(chain.from_iterable(item.recipes for item in dependencies)) + (recipe,)
    cost = RecipeCost(
        operations=sum(item.cost.operations for item in dependencies) + 1,
        sources=sum(item.cost.sources for item in dependencies),
        depth=max(item.cost.depth for item in dependencies) + 1,
        reused_nodes=max(len(combined) - len({item.id for item in combined}), 0),
    )
    return SolvedRecipe(ref=ref, recipes=combined, cost=cost)


def merge_solved_recipe_rows_unique_ids(
    dependencies: tuple[SolvedRecipe, ...],
) -> tuple[SourceRecipe | OperationRecipe, ...]:
    """여러 SolvedRecipe의 ``recipes`` 행을 id 순서대로 합치되, 이미 본 id는 건너뛴다."""
    merged: list[SourceRecipe | OperationRecipe] = []
    seen_ids: set[str] = set()
    for dependency in dependencies:
        for item in dependency.recipes:
            if item.id in seen_ids:
                continue
            merged.append(item)
            seen_ids.add(item.id)
    return tuple(merged)


def _count_dependency_recipe_id_repeats_across_branches(
    dependencies: tuple[SolvedRecipe, ...],
) -> int:
    """의존 브랜치를 순서대로 훑을 때 이미 등장한 id 재등장 횟수(겹치는 서브그래프용)."""
    seen_ids: set[str] = set()
    duplicate_count = 0
    for dependency in dependencies:
        for item in dependency.recipes:
            if item.id in seen_ids:
                duplicate_count += 1
                continue
            seen_ids.add(item.id)
    return duplicate_count


def build_binary_operation_solution_overlapping_deps(
    ctx: SolveContext,
    *,
    operation_type: OperationType,
    left: SolvedRecipe,
    right: SolvedRecipe,
    outputs: tuple[Shape, ...],
    selected_output_index: int,
    label: str,
    description: str,
) -> SolvedRecipe:
    """
    이항 연산 한 단계를 올릴 때, ``right`` 가 ``left`` 의 레시피 행을 그대로 포함할 수 있다.

    ``build_operation_solution`` 의 ``chain`` 병합은 이런 중복 id를 제거하지 않아
    prebuilt checker 등에서 ``recipes`` 가 비대해지므로, 여기서는 id 기준으로 합친다.
    """
    recipe = OperationRecipe(
        id=ctx.allocate_id("op"),
        operation_type=operation_type,
        inputs=(left.ref, right.ref),
        outputs=outputs,
        label=label,
        description=description,
    )
    combined = merge_solved_recipe_rows_unique_ids((left, right)) + (recipe,)
    ref = RecipeRef(
        recipe_id=recipe.id,
        output_index=selected_output_index,
        shape=outputs[selected_output_index],
    )
    cross_repeats = _count_dependency_recipe_id_repeats_across_branches((left, right))
    cost = RecipeCost(
        operations=sum(isinstance(item, OperationRecipe) for item in combined),
        sources=sum(isinstance(item, SourceRecipe) for item in combined),
        depth=max(left.cost.depth, right.cost.depth) + 1,
        reused_nodes=left.cost.reused_nodes + right.cost.reused_nodes + cross_repeats,
    )
    return SolvedRecipe(ref=ref, recipes=combined, cost=cost)


def is_uncolored_full_source(shape: Shape) -> bool:
    if not shape.is_single_layer():
        return False
    parts = shape.non_empty_parts()
    return (
        len(parts) == 4
        and len({part.kind for part in parts}) == 1
        and all(part.color == "u" for part in parts)
    )


def uniform_non_empty_color(shape: Shape) -> str | None:
    colors = {part.color for part in shape.non_empty_parts()}
    if len(colors) != 1:
        return None
    color = next(iter(colors))
    return None if color == "u" else color


def paint_shape(shape: Shape, color: str) -> Shape:
    return Shape(
        layers=tuple(
            ShapeLayer(
                quadrants=(
                    (
                        layer.quadrants[0]
                        if layer.quadrants[0].is_empty
                        else ShapePart(
                            layer.quadrants[0].kind,
                            color,
                            layer.quadrants[0].material,
                        )
                    ),
                    (
                        layer.quadrants[1]
                        if layer.quadrants[1].is_empty
                        else ShapePart(
                            layer.quadrants[1].kind,
                            color,
                            layer.quadrants[1].material,
                        )
                    ),
                    (
                        layer.quadrants[2]
                        if layer.quadrants[2].is_empty
                        else ShapePart(
                            layer.quadrants[2].kind,
                            color,
                            layer.quadrants[2].material,
                        )
                    ),
                    (
                        layer.quadrants[3]
                        if layer.quadrants[3].is_empty
                        else ShapePart(
                            layer.quadrants[3].kind,
                            color,
                            layer.quadrants[3].material,
                        )
                    ),
                )
            )
            for layer in shape.layers
        )
    ).strip_top_empty_layers()


def split_halves(shape: Shape) -> tuple[Shape, Shape]:
    layer = shape.layers[0]
    left = Shape(
        layers=(
            ShapeLayer(quadrants=(layer.quadrants[0], layer.quadrants[1], EMPTY_PART, EMPTY_PART)),
        )
    )
    right = Shape(
        layers=(
            ShapeLayer(quadrants=(EMPTY_PART, EMPTY_PART, layer.quadrants[2], layer.quadrants[3])),
        )
    )
    return left.strip_top_empty_layers(), right.strip_top_empty_layers()


def single_quadrant_shapes(shape: Shape) -> list[Shape]:
    layer = shape.layers[0]
    shapes: list[Shape] = []
    for index, part in enumerate(layer.quadrants):
        if part.is_empty:
            continue
        quadrants = [EMPTY_PART, EMPTY_PART, EMPTY_PART, EMPTY_PART]
        quadrants[index] = part
        shapes.append(
            Shape(
                layers=(
                    ShapeLayer(quadrants=(quadrants[0], quadrants[1], quadrants[2], quadrants[3])),
                )
            )
        )
    return shapes


def is_empty_shape(shape: Shape) -> bool:
    return not shape.non_empty_parts()


def is_uncolored_single_kind(shape: Shape) -> bool:
    parts = shape.non_empty_parts()
    if not parts or any(part.color != "u" for part in parts):
        return False
    return len({part.kind for part in parts}) == 1
