from __future__ import annotations

from dataclasses import dataclass
from itertools import chain

from django_apps.shapez_core.domain.shape import (
    EMPTY_PART,
    Shape,
    ShapeLayer,
    ShapePart,
)
from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.recipe import (
    OperationRecipe,
    RecipeCost,
    RecipeRef,
    SolveContext,
    SolvedRecipe,
    SourceRecipe,
)
from django_apps.shapez_solver.services.operation_engine import OperationEngine


class PlannerError(Exception):
    code = "PLANNER_ERROR"

    def __init__(self, message: str, *, details: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UnsupportedTargetError(PlannerError):
    code = "UNSUPPORTED_TARGET"


class CycleDetectedError(PlannerError):
    code = "CYCLE_DETECTED"


@dataclass(frozen=True, slots=True)
class PlannerRequest:
    target_shape: Shape
    target_rate_per_min: float


@dataclass(frozen=True, slots=True)
class PlannerResult:
    required_inputs: tuple[str, ...]


class PlannerService:
    def __init__(self) -> None:
        self.operation_engine = OperationEngine()

    def plan(self, request: PlannerRequest) -> PlannerResult:
        recipe = self.solve_shape(request.target_shape, SolveContext())
        sources = tuple(
            recipe_item.shape.canonical_code
            for recipe_item in recipe.recipes
            if isinstance(recipe_item, SourceRecipe)
        )
        return PlannerResult(required_inputs=sources)

    def solve_shape(self, target: Shape, ctx: SolveContext) -> SolvedRecipe:
        key = target.canonical_code
        cached = ctx.memo.get(key)
        if cached is not None:
            return cached
        if target.has_unsupported_materials():
            raise UnsupportedTargetError(
                "This target requires pin or crystal mechanics that are not supported yet.",
                details={"target_shape_code": key},
            )
        direct_source = self.try_source(target, ctx)
        if direct_source is not None:
            ctx.memo[key] = direct_source
            return direct_source
        if key in ctx.visiting:
            raise CycleDetectedError(f"cycle detected while solving {key}", details={"target": key})

        ctx.visiting.add(key)
        try:
            candidates = [
                self.try_rotation(target, ctx),
                self.try_stack_layers(target, ctx),
                self.try_paint(target, ctx),
                self.try_assemble_halves(target, ctx),
                self.try_assemble_quadrants(target, ctx),
                self.try_cut_from_source(target, ctx),
            ]
            valid = [
                candidate
                for candidate in candidates
                if candidate is not None
                and self.operation_engine.evaluate(candidate.recipes, candidate.ref) == target
            ]
            if not valid:
                raise UnsupportedTargetError(
                    "The deterministic planner could not build this target with the MVP rule set.",
                    details={"target_shape_code": key},
                )
            best = min(valid, key=lambda item: item.cost.as_sort_key())
            ctx.memo[key] = best
            return best
        finally:
            ctx.visiting.remove(key)

    def try_source(self, target: Shape, ctx: SolveContext) -> SolvedRecipe | None:
        if not _is_uncolored_full_source(target):
            return None
        source = SourceRecipe(id=ctx.allocate_id("source"), shape=target, label="Source")
        ref = RecipeRef(recipe_id=source.id, output_index=0, shape=target)
        return SolvedRecipe(
            ref=ref,
            recipes=(source,),
            cost=RecipeCost(operations=0, sources=1, depth=1, reused_nodes=0),
        )

    def try_rotation(self, target: Shape, ctx: SolveContext) -> SolvedRecipe | None:
        rotations = (
            (OperationType.ROTATE_CW, self.operation_engine.rotate_ccw(target)),
            (OperationType.ROTATE_CCW, self.operation_engine.rotate_cw(target)),
            (OperationType.ROTATE_180, self.operation_engine.rotate_180(target)),
        )
        candidates: list[SolvedRecipe] = []
        target_key = target.canonical_code
        for operation_type, base_shape in rotations:
            if base_shape.canonical_code >= target_key:
                continue
            base = self.solve_shape(base_shape, ctx)
            candidates.append(
                self._build_operation_solution(
                    ctx,
                    operation_type=operation_type,
                    inputs=(base.ref,),
                    outputs=self.operation_engine.apply(operation_type, (base.ref.shape,)),
                    selected_output_index=0,
                    label=OPERATION_CATALOG[operation_type].label,
                    description=OPERATION_CATALOG[operation_type].description,
                    dependencies=(base,),
                )
            )
        return min(candidates, key=lambda item: item.cost.as_sort_key()) if candidates else None

    def try_stack_layers(self, target: Shape, ctx: SolveContext) -> SolvedRecipe | None:
        if len(target.layers) <= 1:
            return None
        current = self.solve_shape(Shape(layers=(target.layers[0],)), ctx)
        for next_layer in target.layers[1:]:
            top = self.solve_shape(Shape(layers=(next_layer,)), ctx)
            current = self._build_operation_solution(
                ctx,
                operation_type=OperationType.STACKER,
                inputs=(current.ref, top.ref),
                outputs=self.operation_engine.apply(
                    OperationType.STACKER,
                    (current.ref.shape, top.ref.shape),
                ),
                selected_output_index=0,
                label=OPERATION_CATALOG[OperationType.STACKER].label,
                description=OPERATION_CATALOG[OperationType.STACKER].description,
                dependencies=(current, top),
            )
        return current

    def try_paint(self, target: Shape, ctx: SolveContext) -> SolvedRecipe | None:
        color = _uniform_non_empty_color(target)
        if color is None:
            return None
        skeleton = _paint_shape(target, "u")
        if skeleton.canonical_code == target.canonical_code:
            return None
        base = self.solve_shape(skeleton, ctx)
        return self._build_operation_solution(
            ctx,
            operation_type=OperationType.PAINTER,
            inputs=(base.ref,),
            outputs=self.operation_engine.apply(
                OperationType.PAINTER,
                (base.ref.shape,),
                color=color,
            ),
            selected_output_index=0,
            label=f"{OPERATION_CATALOG[OperationType.PAINTER].label} ({color})",
            description=f"Paint the shape {color}.",
            dependencies=(base,),
            color=color,
        )

    def try_assemble_halves(self, target: Shape, ctx: SolveContext) -> SolvedRecipe | None:
        if not target.is_single_layer():
            return None
        left_half, right_half = _split_halves(target)
        if _is_empty_shape(left_half) or _is_empty_shape(right_half):
            return None
        left = self.solve_shape(left_half, ctx)
        right = self.solve_shape(right_half, ctx)
        outputs = self.operation_engine.apply(
            OperationType.SWAPPER,
            (left.ref.shape, right.ref.shape),
        )
        if outputs[0] != target:
            return None
        return self._build_operation_solution(
            ctx,
            operation_type=OperationType.SWAPPER,
            inputs=(left.ref, right.ref),
            outputs=outputs,
            selected_output_index=0,
            label=OPERATION_CATALOG[OperationType.SWAPPER].label,
            description=OPERATION_CATALOG[OperationType.SWAPPER].description,
            dependencies=(left, right),
        )

    def try_assemble_quadrants(self, target: Shape, ctx: SolveContext) -> SolvedRecipe | None:
        if not target.is_single_layer():
            return None
        quadrant_shapes = _single_quadrant_shapes(target)
        if len(quadrant_shapes) <= 1:
            return None
        solved_parts = [self.solve_shape(shape, ctx) for shape in quadrant_shapes]
        current = solved_parts[0]
        for next_part in solved_parts[1:]:
            outputs = self.operation_engine.apply(
                OperationType.STACKER,
                (current.ref.shape, next_part.ref.shape),
            )
            current = self._build_operation_solution(
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

    def try_cut_from_source(self, target: Shape, ctx: SolveContext) -> SolvedRecipe | None:
        if not target.is_single_layer() or not _is_uncolored_single_kind(target):
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
        source = self.try_source(source_shape, ctx)
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
                    self._derive_cut_output(ctx, recipe, 0),
                    self._derive_cut_output(ctx, recipe, 1),
                    self._derive_rotation(ctx, recipe, OperationType.ROTATE_CW),
                    self._derive_rotation(ctx, recipe, OperationType.ROTATE_CCW),
                    self._derive_rotation(ctx, recipe, OperationType.ROTATE_180),
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
        self,
        ctx: SolveContext,
        recipe: SolvedRecipe,
        output_index: int,
    ) -> SolvedRecipe:
        outputs = self.operation_engine.apply(OperationType.CUTTER, (recipe.ref.shape,))
        return self._build_operation_solution(
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
        self,
        ctx: SolveContext,
        recipe: SolvedRecipe,
        operation_type: OperationType,
    ) -> SolvedRecipe:
        outputs = self.operation_engine.apply(operation_type, (recipe.ref.shape,))
        return self._build_operation_solution(
            ctx,
            operation_type=operation_type,
            inputs=(recipe.ref,),
            outputs=outputs,
            selected_output_index=0,
            label=OPERATION_CATALOG[operation_type].label,
            description=OPERATION_CATALOG[operation_type].description,
            dependencies=(recipe,),
        )

    def _build_operation_solution(
        self,
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


def _is_uncolored_full_source(shape: Shape) -> bool:
    if not shape.is_single_layer():
        return False
    parts = shape.non_empty_parts()
    return (
        len(parts) == 4
        and len({part.kind for part in parts}) == 1
        and all(part.color == "u" for part in parts)
    )


def _uniform_non_empty_color(shape: Shape) -> str | None:
    colors = {part.color for part in shape.non_empty_parts()}
    if len(colors) != 1:
        return None
    color = next(iter(colors))
    return None if color == "u" else color


def _paint_shape(shape: Shape, color: str) -> Shape:
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


def _split_halves(shape: Shape) -> tuple[Shape, Shape]:
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


def _single_quadrant_shapes(shape: Shape) -> list[Shape]:
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


def _is_empty_shape(shape: Shape) -> bool:
    return not shape.non_empty_parts()


def _is_uncolored_single_kind(shape: Shape) -> bool:
    parts = shape.non_empty_parts()
    if not parts or any(part.color != "u" for part in parts):
        return False
    return len({part.kind for part in parts}) == 1
