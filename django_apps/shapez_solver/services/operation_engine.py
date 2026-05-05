from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_core.domain.shape import EMPTY_PART, Shape, ShapeLayer, ShapePart
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.recipe import OperationRecipe, RecipeRef, SourceRecipe
from django_apps.shapez_solver.services.color_mix_semantics import mix_color_pair


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
        if operation_type == OperationType.HALF_DESTROYER:
            return (self.half_destroyer(inputs[0]),)
        if operation_type == OperationType.SPLITTER:
            return self.splitter(inputs[0])
        if operation_type == OperationType.PIN_PUSHER:
            return (self.pin_pusher(inputs[0]),)
        if operation_type == OperationType.SWAPPER:
            return self.swapper(inputs[0], inputs[1])
        if operation_type == OperationType.STACKER:
            return (self.stacker(inputs[0], inputs[1]),)
        if operation_type == OperationType.PAINTER:
            if color is None:
                raise ValueError("painter requires an explicit color")
            return (self.painter(inputs[0], color),)
        if operation_type == OperationType.COLOR_MIXER:
            return (self.color_mixer(inputs[0], inputs[1]),)
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

    def half_destroyer(self, shape: Shape) -> Shape:
        """Keeps the left cutter lane only (same split geometry as :meth:`cut`)."""

        left, _right = self.cut(shape)
        return left

    def splitter(self, shape: Shape) -> tuple[Shape, Shape]:
        """One input, two outputs: identical copy on each lane (belt splitter)."""

        return (shape, shape)

    def pin_pusher(self, shape: Shape) -> Shape:
        """Add a full pin layer under the shape (lifts the shape in the layer model)."""

        pin_bottom = ShapeLayer(
            quadrants=(
                ShapePart(kind="P", color="-", material="pin"),
                ShapePart(kind="P", color="-", material="pin"),
                ShapePart(kind="P", color="-", material="pin"),
                ShapePart(kind="P", color="-", material="pin"),
            )
        )
        return Shape(layers=(pin_bottom, *shape.layers)).strip_top_empty_layers()

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

    def color_mixer(self, left: Shape, right: Shape) -> Shape:
        """두 shape의 동일 레이어·사분면에서 색만 혼합한다(종류는 같아야 한다)."""

        if len(left.layers) != len(right.layers):
            raise ValueError("color_mixer requires matching layer counts")
        new_layers: list[ShapeLayer] = []
        for left_layer, right_layer in zip(left.layers, right.layers, strict=True):
            quads: list[ShapePart] = []
            for la, lb in zip(left_layer.quadrants, right_layer.quadrants, strict=True):
                if la.is_empty and lb.is_empty:
                    quads.append(EMPTY_PART)
                elif la.is_empty:
                    quads.append(lb)
                elif lb.is_empty:
                    quads.append(la)
                else:
                    if la.kind != lb.kind:
                        raise ValueError("color_mixer requires matching part kinds per quadrant")
                    if la.is_pin or lb.is_pin or la.is_crystal or lb.is_crystal:
                        raise ValueError("color_mixer MVP does not support pins or crystals")
                    mixed = mix_color_pair(la.color, lb.color)
                    quads.append(ShapePart(kind=la.kind, color=mixed, material=la.material))
            new_layers.append(ShapeLayer(quadrants=(quads[0], quads[1], quads[2], quads[3])))
        return Shape(layers=tuple(new_layers)).strip_top_empty_layers()

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
