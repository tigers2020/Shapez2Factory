from __future__ import annotations

import time
from dataclasses import dataclass

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_solver.domain.batch_plan import BatchPlan
from django_apps.shapez_solver.domain.factory_demand import (
    BaseDemand,
    UnsupportedFactoryDemandError,
    compute_factory_batch,
    inventory_search_goal_shape_code,
    inventory_search_rejects_target_for_missing_paint,
)
from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.recipe import SolvedRecipe
from django_apps.shapez_solver.dto.solver_graph import SolverGraph
from django_apps.shapez_solver.services.combined_action_generator import CombinedActionGenerator
from django_apps.shapez_solver.services.flow_graph_builder import build_solver_graph_from_batch_plan
from django_apps.shapez_solver.services.inventory_search_solver import (
    InventorySearchError,
    InventorySearchRequest,
    InventorySearchSolver,
)
from django_apps.shapez_solver.services.macro_action_generator import (
    CatalogAwareMacroActionGenerator,
)
from django_apps.shapez_solver.services.planner_service import UnsupportedTargetError
from django_apps.shapez_solver.services.solver_types import SolveStep


def _steps_from_batch_plan(plan: BatchPlan) -> tuple[SolveStep, ...]:
    steps: list[SolveStep] = []
    for run in plan.steps:
        catalog = OPERATION_CATALOG[run.operation]
        steps.append(
            SolveStep(
                id=run.id,
                operation_type=run.operation.value,
                title=catalog.label,
                description=catalog.description,
                input_shape_codes=run.inputs,
                output_shape_codes=run.outputs,
            )
        )
    return tuple(steps)


@dataclass(frozen=True, slots=True)
class FactoryThroughputRequest:
    target_shape: Shape
    max_depth: int = 12
    solver_timeout_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class FactoryThroughputResult:
    found: bool
    target_shape: str
    target_count: int
    solved_recipe: SolvedRecipe | None
    base_demands: tuple[BaseDemand, ...] = ()
    graph: SolverGraph | None = None
    materialized_graph: SolverGraph | None = None
    warnings: tuple[str, ...] = ()
    steps: tuple[SolveStep, ...] = ()
    batch_plan: BatchPlan | None = None
    solver_mode: str = "inventory_search"


class FactoryThroughputService:
    def solve(self, request: FactoryThroughputRequest) -> FactoryThroughputResult:
        if request.target_shape.has_unsupported_materials():
            raise UnsupportedTargetError(
                "This target requires pin or crystal mechanics that are not supported yet.",
                details={"target_shape_code": request.target_shape.canonical_code},
            )

        warnings_list: list[str] = []
        batch = None
        try:
            batch = compute_factory_batch(request.target_shape)
            base_demands = batch.base_demands
            target_count = batch.target_count
        except UnsupportedFactoryDemandError as exc:
            return FactoryThroughputResult(
                found=False,
                target_shape=request.target_shape.canonical_code,
                target_count=1,
                solved_recipe=None,
                base_demands=(),
                graph=None,
                materialized_graph=None,
                warnings=(f"factory_batch_unsupported: {exc}",),
                steps=(),
                batch_plan=None,
                solver_mode="inventory_search",
            )

        assert batch is not None
        if inventory_search_rejects_target_for_missing_paint(request.target_shape):
            return FactoryThroughputResult(
                found=False,
                target_shape=request.target_shape.canonical_code,
                target_count=batch.target_count,
                solved_recipe=None,
                base_demands=batch.base_demands,
                graph=None,
                materialized_graph=None,
                warnings=(
                    "inventory_search_skips_monochrome_paint: " "painter not in inventory search",
                ),
                steps=(),
                batch_plan=None,
                solver_mode="inventory_search",
            )
        goal_code = inventory_search_goal_shape_code(request.target_shape)
        deadline = None
        if request.solver_timeout_seconds is not None and request.solver_timeout_seconds > 0:
            deadline = time.monotonic() + request.solver_timeout_seconds
        inv_request = InventorySearchRequest(
            target_code=goal_code,
            target_count=target_count,
            source_counts=dict(batch.base_source_counts),
            max_states=25_000,
            max_steps=28,
            deadline_monotonic=deadline,
        )
        try:
            action_generator = CombinedActionGenerator(macros=CatalogAwareMacroActionGenerator())
            plan = InventorySearchSolver(action_generator).solve(inv_request)
            graph = build_solver_graph_from_batch_plan(
                plan,
                display_target_shape_code=request.target_shape.canonical_code,
                display_target_shape=request.target_shape,
            )
            return FactoryThroughputResult(
                found=True,
                target_shape=request.target_shape.canonical_code,
                target_count=target_count,
                solved_recipe=None,
                base_demands=base_demands,
                graph=graph,
                materialized_graph=None,
                warnings=tuple(warnings_list),
                steps=_steps_from_batch_plan(plan),
                batch_plan=plan,
                solver_mode="inventory_search",
            )
        except InventorySearchError as exc:
            warnings_list.append(f"inventory_search_failed: {exc}")
            return FactoryThroughputResult(
                found=False,
                target_shape=request.target_shape.canonical_code,
                target_count=target_count,
                solved_recipe=None,
                base_demands=base_demands,
                graph=None,
                materialized_graph=None,
                warnings=tuple(warnings_list),
                steps=(),
                batch_plan=None,
                solver_mode="inventory_search",
            )


__all__ = [
    "FactoryThroughputRequest",
    "FactoryThroughputResult",
    "FactoryThroughputService",
]
