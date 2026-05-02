from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_solver.domain.factory_demand import (
    BaseDemand,
    UnsupportedFactoryDemandError,
    compute_base_demands,
)
from django_apps.shapez_solver.domain.recipe import SolvedRecipe
from django_apps.shapez_solver.dto.solver_graph import SolverGraph
from django_apps.shapez_solver.services.solve_pipeline import SolveStep, solve_recipe_pipeline


@dataclass(frozen=True, slots=True)
class FactoryThroughputRequest:
    target_shape: Shape
    target_count: int = 1
    max_depth: int = 12


@dataclass(frozen=True, slots=True)
class FactoryThroughputResult:
    found: bool
    target_shape: str
    target_count: int
    solved_recipe: SolvedRecipe
    base_demands: tuple[BaseDemand, ...] = ()
    graph: SolverGraph | None = None
    warnings: tuple[str, ...] = ()
    steps: tuple[SolveStep, ...] = ()


class FactoryThroughputService:
    def solve(self, request: FactoryThroughputRequest) -> FactoryThroughputResult:
        warnings: tuple[str, ...] = ()
        try:
            base_demands = compute_base_demands(
                request.target_shape,
                target_count=request.target_count,
            )
        except UnsupportedFactoryDemandError:
            base_demands = ()
            warnings = (
                "Base demands are available only for single-layer targets without "
                "pin or crystal materials.",
            )

        pipeline_result = solve_recipe_pipeline(
            request.target_shape,
            target_count=request.target_count,
            base_demands=base_demands,
        )
        return FactoryThroughputResult(
            found=True,
            target_shape=request.target_shape.canonical_code,
            target_count=request.target_count,
            solved_recipe=pipeline_result.solved_recipe,
            base_demands=base_demands,
            graph=pipeline_result.graph,
            warnings=warnings,
            steps=pipeline_result.steps,
        )


__all__ = [
    "FactoryThroughputRequest",
    "FactoryThroughputResult",
    "FactoryThroughputService",
]
