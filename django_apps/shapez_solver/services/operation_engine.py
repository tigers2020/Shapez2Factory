from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.recipe import OperationRecipe, RecipeRef, SourceRecipe
from django_apps.shapez_solver.services.engine_operation_helpers import (
    color_mixer_fluids,
    crystal_generator_output,
    cutter_halves,
    half_destroyer_shape,
    painter_output,
    painter_with_fluid_target,
    pin_pusher_output,
    rotate_shape,
    splitter_outputs,
    stacker_output,
    swapper_outputs,
)


@dataclass(frozen=True, slots=True)
class EvaluatedRecipe:
    output: Shape


class OperationEngine:
    def apply(
        self,
        operation_type: OperationType,
        inputs: tuple[Shape, ...],
        color: str | None = None,
    ) -> tuple[Shape, ...]:
        if operation_type in (
            OperationType.ROTATE_CW,
            OperationType.ROTATE_CCW,
            OperationType.ROTATE_180,
        ):
            return (rotate_shape(inputs[0], operation_type),)
        if operation_type == OperationType.CUTTER:
            return cutter_halves(inputs[0])
        if operation_type == OperationType.HALF_DESTROYER:
            return (half_destroyer_shape(inputs[0]),)
        if operation_type == OperationType.SPLITTER:
            return splitter_outputs(inputs[0])
        if operation_type == OperationType.PIN_PUSHER:
            return (pin_pusher_output(inputs[0]),)
        if operation_type == OperationType.SWAPPER:
            return swapper_outputs(inputs[0], inputs[1])
        if operation_type == OperationType.STACKER:
            return (stacker_output(inputs[0], inputs[1]),)
        if operation_type == OperationType.PAINTER:
            if len(inputs) == 2:
                return (painter_with_fluid_target(inputs[0], inputs[1]),)
            if color is None:
                raise ValueError(
                    "painter requires an explicit color when only one shape input is given",
                )
            return (painter_output(inputs[0], color),)
        if operation_type == OperationType.COLOR_MIXER:
            return (color_mixer_fluids(inputs[0], inputs[1]),)
        if operation_type == OperationType.CRYSTAL_GENERATOR:
            if color is None:
                raise ValueError("crystal_generator requires an explicit color")
            if len(inputs) < 1:
                raise ValueError("crystal_generator requires at least one input shape")
            return (crystal_generator_output(inputs[0], color),)
        raise ValueError(f"unsupported operation: {operation_type}")

    def evaluate(
        self,
        recipes: tuple[SourceRecipe | OperationRecipe, ...],
        ref: RecipeRef,
    ) -> Shape:
        outputs: dict[tuple[str, int], Shape] = {}
        recipes_by_id = {recipe.id: recipe for recipe in recipes}

        def resolve(target: RecipeRef) -> Shape:
            key = (target.recipe_id, target.output_index)
            cached = outputs.get(key)
            if cached is not None:
                return cached

            recipe = recipes_by_id[target.recipe_id]
            if isinstance(recipe, SourceRecipe):
                outputs[key] = recipe.shape
                return recipe.shape

            input_shapes = tuple(resolve(input_ref) for input_ref in recipe.inputs)
            result_shapes = self.apply(recipe.operation_type, input_shapes, color=recipe.color)
            for index, result in enumerate(result_shapes):
                outputs[(recipe.id, index)] = result
            return outputs[key]

        return resolve(ref)

    def rotate_cw(self, shape: Shape) -> Shape:
        return rotate_shape(shape, OperationType.ROTATE_CW)

    def rotate_ccw(self, shape: Shape) -> Shape:
        return rotate_shape(shape, OperationType.ROTATE_CCW)

    def rotate_180(self, shape: Shape) -> Shape:
        return rotate_shape(shape, OperationType.ROTATE_180)

    def cut(self, shape: Shape) -> tuple[Shape, Shape]:
        return cutter_halves(shape)

    def half_destroyer(self, shape: Shape) -> Shape:
        return half_destroyer_shape(shape)

    def splitter(self, shape: Shape) -> tuple[Shape, Shape]:
        return splitter_outputs(shape)

    def pin_pusher(self, shape: Shape) -> Shape:
        return pin_pusher_output(shape)

    def swapper(self, left_shape: Shape, right_shape: Shape) -> tuple[Shape, Shape]:
        return swapper_outputs(left_shape, right_shape)

    def stacker(self, bottom: Shape, top: Shape) -> Shape:
        return stacker_output(bottom, top)

    def painter(self, shape: Shape, color: str) -> Shape:
        return painter_output(shape, color)

    def color_mixer(self, left: Shape, right: Shape) -> Shape:
        return color_mixer_fluids(left, right)
