from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_solver.domain.recipe import SolveContext, SolvedRecipe, SourceRecipe
from django_apps.shapez_solver.services.operation_engine import OperationEngine
from django_apps.shapez_solver.services.planner_rules import (
    try_assemble_halves,
    try_assemble_quadrants,
    try_cut_from_source,
    try_paint,
    try_rotation,
    try_source,
    try_stack_layers,
)

type RuleAttempt = Callable[
    [Shape, SolveContext, Callable[[Shape, SolveContext], SolvedRecipe], OperationEngine],
    SolvedRecipe | None,
]


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
        self.rule_attempts: tuple[RuleAttempt, ...] = (
            _try_rotation,
            _try_stack_layers,
            _try_paint,
            _try_assemble_halves,
            _try_assemble_quadrants,
            _try_cut_from_source,
        )

    def plan(self, request: PlannerRequest) -> PlannerResult:
        recipe = self.solve_shape(request.target_shape, SolveContext())
        return PlannerResult(required_inputs=_source_codes(recipe))

    def solve_shape(self, target: Shape, ctx: SolveContext) -> SolvedRecipe:
        key = target.canonical_code
        cached = ctx.memo.get(key)
        if cached is not None:
            return cached
        _validate_supported_target(target)

        direct_source = try_source(target, ctx)
        if direct_source is not None:
            ctx.memo[key] = direct_source
            return direct_source
        if key in ctx.visiting:
            raise CycleDetectedError(f"cycle detected while solving {key}", details={"target": key})

        ctx.visiting.add(key)
        try:
            best = self._best_candidate(target, ctx)
            ctx.memo[key] = best
            return best
        finally:
            ctx.visiting.remove(key)

    def _best_candidate(self, target: Shape, ctx: SolveContext) -> SolvedRecipe:
        valid = [
            candidate
            for candidate in self._candidate_solutions(target, ctx)
            if self.operation_engine.evaluate(candidate.recipes, candidate.ref) == target
        ]
        if not valid:
            raise UnsupportedTargetError(
                "The deterministic planner could not build this target with the MVP rule set.",
                details={"target_shape_code": target.canonical_code},
            )
        return min(valid, key=lambda item: item.cost.as_sort_key())

    def _candidate_solutions(self, target: Shape, ctx: SolveContext) -> list[SolvedRecipe]:
        return [
            candidate
            for candidate in (
                rule(target, ctx, self.solve_shape, self.operation_engine)
                for rule in self.rule_attempts
            )
            if candidate is not None
        ]


def _source_codes(recipe: SolvedRecipe) -> tuple[str, ...]:
    return tuple(
        recipe_item.shape.canonical_code
        for recipe_item in recipe.recipes
        if isinstance(recipe_item, SourceRecipe)
    )


def _validate_supported_target(target: Shape) -> None:
    if target.has_unsupported_materials():
        raise UnsupportedTargetError(
            "This target requires pin or crystal mechanics that are not supported yet.",
            details={"target_shape_code": target.canonical_code},
        )


def _try_rotation(
    target: Shape,
    ctx: SolveContext,
    solve_shape: Callable[[Shape, SolveContext], SolvedRecipe],
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    return try_rotation(
        target,
        ctx,
        solve_shape=solve_shape,
        operation_engine=operation_engine,
    )


def _try_stack_layers(
    target: Shape,
    ctx: SolveContext,
    solve_shape: Callable[[Shape, SolveContext], SolvedRecipe],
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    return try_stack_layers(
        target,
        ctx,
        solve_shape=solve_shape,
        operation_engine=operation_engine,
    )


def _try_paint(
    target: Shape,
    ctx: SolveContext,
    solve_shape: Callable[[Shape, SolveContext], SolvedRecipe],
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    return try_paint(
        target,
        ctx,
        solve_shape=solve_shape,
        operation_engine=operation_engine,
    )


def _try_assemble_halves(
    target: Shape,
    ctx: SolveContext,
    solve_shape: Callable[[Shape, SolveContext], SolvedRecipe],
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    return try_assemble_halves(
        target,
        ctx,
        solve_shape=solve_shape,
        operation_engine=operation_engine,
    )


def _try_assemble_quadrants(
    target: Shape,
    ctx: SolveContext,
    solve_shape: Callable[[Shape, SolveContext], SolvedRecipe],
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    return try_assemble_quadrants(
        target,
        ctx,
        solve_shape=solve_shape,
        operation_engine=operation_engine,
    )


def _try_cut_from_source(
    target: Shape,
    ctx: SolveContext,
    solve_shape: Callable[[Shape, SolveContext], SolvedRecipe],
    operation_engine: OperationEngine,
) -> SolvedRecipe | None:
    del solve_shape
    return try_cut_from_source(
        target,
        ctx,
        operation_engine=operation_engine,
    )
