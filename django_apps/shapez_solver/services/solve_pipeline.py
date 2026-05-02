from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_solver.domain.recipe import SolveContext, SolvedRecipe
from django_apps.shapez_solver.dto.solver_graph import SolverGraph
from django_apps.shapez_solver.services.operation_engine import OperationEngine
from django_apps.shapez_solver.services.planner_service import PlannerService
from django_apps.shapez_solver.services.recipe_graph_builder import RecipeGraphBuilder


class SolverValidationError(Exception):
    code = "SOLVER_VALIDATION_ERROR"

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(f"expected {expected}, got {actual}")
        self.expected = expected
        self.actual = actual


@dataclass(frozen=True, slots=True)
class SolveStep:
    id: str
    operation_type: str
    title: str
    description: str
    input_shape_codes: tuple[str, ...]
    output_shape_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SolvePipelineResult:
    solved_recipe: SolvedRecipe
    graph: SolverGraph
    steps: tuple[SolveStep, ...]


def solve_recipe_pipeline(
    target_shape: Shape,
    *,
    target_count: int = 1,
    base_demands: tuple[object, ...] = (),
) -> SolvePipelineResult:
    planner = PlannerService()
    operation_engine = OperationEngine()
    graph_builder = RecipeGraphBuilder()

    solved = planner.solve_shape(target_shape, SolveContext())
    final_shape = operation_engine.evaluate(solved.recipes, solved.ref)
    if final_shape != target_shape:
        raise SolverValidationError(
            expected=target_shape.canonical_code,
            actual=final_shape.canonical_code,
        )

    return SolvePipelineResult(
        solved_recipe=solved,
        graph=graph_builder.build(
            solved,
            target_count=target_count,
            base_demands=base_demands,
        ),
        steps=_build_steps(solved),
    )


def _build_steps(solved: SolvedRecipe) -> tuple[SolveStep, ...]:
    from django_apps.shapez_solver.domain.recipe import OperationRecipe

    steps: list[SolveStep] = []
    for recipe in solved.recipes:
        if not isinstance(recipe, OperationRecipe):
            continue
        steps.append(
            SolveStep(
                id=recipe.id,
                operation_type=recipe.operation_type.value,
                title=recipe.label,
                description=recipe.description,
                input_shape_codes=tuple(ref.shape.canonical_code for ref in recipe.inputs),
                output_shape_codes=tuple(output.canonical_code for output in recipe.outputs),
            )
        )
    return tuple(steps)


__all__ = [
    "SolvePipelineResult",
    "SolveStep",
    "SolverValidationError",
    "solve_recipe_pipeline",
]
