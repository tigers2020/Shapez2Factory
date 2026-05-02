from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_solver.domain.recipe import SolveContext
from django_apps.shapez_solver.dto.solver_graph import SolverGraph
from django_apps.shapez_solver.services.graph_builder import GraphBuilder
from django_apps.shapez_solver.services.operation_engine import OperationEngine
from django_apps.shapez_solver.services.planner_service import (
    PlannerService,
)


class SolverValidationError(Exception):
    code = "SOLVER_VALIDATION_ERROR"

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(f"expected {expected}, got {actual}")
        self.expected = expected
        self.actual = actual


@dataclass(frozen=True, slots=True)
class SolverRequest:
    target_shape: Shape
    max_depth: int = 12


@dataclass(frozen=True, slots=True)
class SolveStep:
    id: str
    operation_type: str
    title: str
    description: str
    input_shape_codes: tuple[str, ...]
    output_shape_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SolverResult:
    found: bool
    target_shape: str
    graph: SolverGraph | None = None
    warnings: tuple[str, ...] = ()
    steps: tuple[SolveStep, ...] = ()


class SolverService:
    def __init__(self) -> None:
        self.planner = PlannerService()
        self.operation_engine = OperationEngine()
        self.graph_builder = GraphBuilder()

    def solve(self, request: SolverRequest) -> SolverResult:
        solved = self.planner.solve_shape(request.target_shape, SolveContext())
        final_shape = self.operation_engine.evaluate(solved.recipes, solved.ref)
        if final_shape != request.target_shape:
            raise SolverValidationError(
                expected=request.target_shape.canonical_code,
                actual=final_shape.canonical_code,
            )
        graph = self.graph_builder.build(solved)
        return SolverResult(
            found=True,
            target_shape=request.target_shape.canonical_code,
            graph=graph,
            warnings=(),
            steps=_build_compat_steps(solved),
        )


def _build_compat_steps(solved: object) -> tuple[SolveStep, ...]:
    from django_apps.shapez_solver.domain.recipe import OperationRecipe, SolvedRecipe

    solved_recipe = solved if isinstance(solved, SolvedRecipe) else None
    if solved_recipe is None:
        return ()
    steps: list[SolveStep] = []
    for recipe in solved_recipe.recipes:
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
    "SolveStep",
    "SolverRequest",
    "SolverResult",
    "SolverService",
    "SolverValidationError",
]
