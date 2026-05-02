from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_core.domain.shape import EMPTY_PART, Shape, ShapeLayer, ShapePart
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.recipe import OperationRecipe, RecipeRef, SourceRecipe


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
        if operation_type == OperationType.ROTATE_CW:
            return (self.rotate_cw(inputs[0]),)
        if operation_type == OperationType.ROTATE_CCW:
            return (self.rotate_ccw(inputs[0]),)
        if operation_type == OperationType.ROTATE_180:
            return (self.rotate_180(inputs[0]),)
        if operation_type == OperationType.CUTTER:
            return self.cut(inputs[0])
        if operation_type == OperationType.SWAPPER:
            return self.swapper(inputs[0], inputs[1])
        if operation_type == OperationType.STACKER:
            return (self.stacker(inputs[0], inputs[1]),)
        if operation_type == OperationType.PAINTER:
            if color is None:
                raise ValueError("painter requires an explicit color")
            return (self.painter(inputs[0], color),)
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
        return Shape(
            layers=tuple(
                ShapeLayer(
                    quadrants=(
                        layer.quadrants[3],
                        layer.quadrants[0],
                        layer.quadrants[1],
                        layer.quadrants[2],
                    )
                )
                for layer in shape.layers
            )
        ).strip_top_empty_layers()

    def rotate_ccw(self, shape: Shape) -> Shape:
        return Shape(
            layers=tuple(
                ShapeLayer(
                    quadrants=(
                        layer.quadrants[1],
                        layer.quadrants[2],
                        layer.quadrants[3],
                        layer.quadrants[0],
                    )
                )
                for layer in shape.layers
            )
        ).strip_top_empty_layers()

    def rotate_180(self, shape: Shape) -> Shape:
        return Shape(
            layers=tuple(
                ShapeLayer(
                    quadrants=(
                        layer.quadrants[2],
                        layer.quadrants[3],
                        layer.quadrants[0],
                        layer.quadrants[1],
                    )
                )
                for layer in shape.layers
            )
        ).strip_top_empty_layers()

    def cut(self, shape: Shape) -> tuple[Shape, Shape]:
        left = Shape(
            layers=tuple(
                ShapeLayer(
                    quadrants=(
                        layer.quadrants[0],
                        layer.quadrants[1],
                        EMPTY_PART,
                        EMPTY_PART,
                    )
                )
                for layer in shape.layers
            )
        ).strip_top_empty_layers()
        right = Shape(
            layers=tuple(
                ShapeLayer(
                    quadrants=(
                        EMPTY_PART,
                        EMPTY_PART,
                        layer.quadrants[2],
                        layer.quadrants[3],
                    )
                )
                for layer in shape.layers
            )
        ).strip_top_empty_layers()
        return left, right

    def swapper(self, left_shape: Shape, right_shape: Shape) -> tuple[Shape, Shape]:
        if len(left_shape.layers) != 1 or len(right_shape.layers) != 1:
            raise ValueError("swapper MVP supports only single-layer shapes")
        left_layer = left_shape.layers[0]
        right_layer = right_shape.layers[0]
        output_a = Shape(
            layers=(
                ShapeLayer(
                    quadrants=(
                        left_layer.quadrants[0],
                        left_layer.quadrants[1],
                        right_layer.quadrants[2],
                        right_layer.quadrants[3],
                    )
                ),
            )
        )
        output_b = Shape(
            layers=(
                ShapeLayer(
                    quadrants=(
                        right_layer.quadrants[0],
                        right_layer.quadrants[1],
                        left_layer.quadrants[2],
                        left_layer.quadrants[3],
                    )
                ),
            )
        )
        return output_a, output_b

    def stacker(self, bottom: Shape, top: Shape) -> Shape:
        if len(bottom.layers) == 1 and len(top.layers) == 1:
            merged = self._merge_disjoint_layers(bottom.layers[0], top.layers[0])
            if merged is not None:
                return Shape(layers=(merged,)).strip_top_empty_layers()
        return Shape(layers=(*bottom.layers, *top.layers)).strip_top_empty_layers()

    def painter(self, shape: Shape, color: str) -> Shape:
        return Shape(
            layers=tuple(
                ShapeLayer(
                    quadrants=(
                        (
                            layer.quadrants[0].with_color(color)
                            if not layer.quadrants[0].is_empty
                            else layer.quadrants[0]
                        ),
                        (
                            layer.quadrants[1].with_color(color)
                            if not layer.quadrants[1].is_empty
                            else layer.quadrants[1]
                        ),
                        (
                            layer.quadrants[2].with_color(color)
                            if not layer.quadrants[2].is_empty
                            else layer.quadrants[2]
                        ),
                        (
                            layer.quadrants[3].with_color(color)
                            if not layer.quadrants[3].is_empty
                            else layer.quadrants[3]
                        ),
                    )
                )
                for layer in shape.layers
            )
        ).strip_top_empty_layers()

    def _merge_disjoint_layers(
        self,
        left: ShapeLayer,
        right: ShapeLayer,
    ) -> ShapeLayer | None:
        quadrants: list[ShapePart] = []
        for left_part, right_part in zip(left.quadrants, right.quadrants, strict=True):
            if not left_part.is_empty and not right_part.is_empty:
                return None
            quadrants.append(left_part if not left_part.is_empty else right_part)
        return ShapeLayer(quadrants=(quadrants[0], quadrants[1], quadrants[2], quadrants[3]))
