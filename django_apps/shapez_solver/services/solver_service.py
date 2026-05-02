from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_solver.dto.solver_graph import SolverGraph
from django_apps.shapez_solver.services import solve_pipeline

SolveStep = solve_pipeline.SolveStep
SolverValidationError = solve_pipeline.SolverValidationError


@dataclass(frozen=True, slots=True)
class SolverRequest:
    target_shape: Shape
    max_depth: int = 12


@dataclass(frozen=True, slots=True)
class SolverResult:
    found: bool
    target_shape: str
    graph: SolverGraph | None = None
    warnings: tuple[str, ...] = ()
    steps: tuple[SolveStep, ...] = ()


class SolverService:
    def solve(self, request: SolverRequest) -> SolverResult:
        pipeline_result = solve_pipeline.solve_recipe_pipeline(request.target_shape)
        return SolverResult(
            found=True,
            target_shape=request.target_shape.canonical_code,
            graph=pipeline_result.graph,
            warnings=(),
            steps=pipeline_result.steps,
        )


__all__ = [
    "SolveStep",
    "SolverRequest",
    "SolverResult",
    "SolverService",
    "SolverValidationError",
]
