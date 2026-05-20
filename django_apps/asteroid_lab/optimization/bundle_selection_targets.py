"""Bundle selection targets: route slot count vs miner bundle budget (Phase I)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.capacity_planner import (
    FLUID_PLATFORMS_PER_GOAL,
    SHAPE_PLATFORMS_PER_GOAL,
)
from django_apps.asteroid_lab.optimization.enums import TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal

DEFAULT_MINERS_PER_SHAPE_ROUTE = SHAPE_PLATFORMS_PER_GOAL


@dataclass(frozen=True, slots=True)
class BundleSelectionTargets:
    """Separates route slot count from bundle selection/commit budget."""

    route_out_count: int
    miners_per_shape_route: int
    pumps_per_fluid_route: int
    target_miner_bundle_count: int
    shape_route_out_count: int
    fluid_route_out_count: int


def compute_bundle_selection_targets(
    route_goals: frozenset[RouteGoal],
    *,
    miners_per_shape_route: int = DEFAULT_MINERS_PER_SHAPE_ROUTE,
    pumps_per_fluid_route: int = FLUID_PLATFORMS_PER_GOAL,
) -> BundleSelectionTargets:
    """Per-goal bundle budget: shape × miners_per_shape_route, fluid × pumps_per_fluid_route."""

    if miners_per_shape_route < 1:
        msg = "miners_per_shape_route must be >= 1"
        raise ValueError(msg)
    if pumps_per_fluid_route < 1:
        msg = "pumps_per_fluid_route must be >= 1"
        raise ValueError(msg)

    shape_count = 0
    fluid_count = 0
    target = 0
    for goal in route_goals:
        if goal.transport_kind == TransportKind.FLUID_PIPE:
            fluid_count += 1
            target += pumps_per_fluid_route
        else:
            shape_count += 1
            target += miners_per_shape_route

    return BundleSelectionTargets(
        route_out_count=len(route_goals),
        miners_per_shape_route=miners_per_shape_route,
        pumps_per_fluid_route=pumps_per_fluid_route,
        target_miner_bundle_count=target,
        shape_route_out_count=shape_count,
        fluid_route_out_count=fluid_count,
    )


def bundle_selection_targets_from_run_config(
    route_goals: frozenset[RouteGoal],
    run_config: dict[str, object] | None,
) -> BundleSelectionTargets:
    """Merge settings default with optional ``SolverRun.config_json`` override."""

    miners_per_shape = miners_per_shape_route_from_settings()
    if run_config:
        from django_apps.asteroid_lab.services.solver_run_config_keys import (
            SOLVER_RUN_CONFIG_MINERS_PER_ROUTE_OUT_KEY,
        )

        raw = run_config.get(SOLVER_RUN_CONFIG_MINERS_PER_ROUTE_OUT_KEY)
        if isinstance(raw, int) and raw > 0:
            miners_per_shape = raw
    return compute_bundle_selection_targets(
        route_goals,
        miners_per_shape_route=miners_per_shape,
    )


def miners_per_shape_route_from_settings() -> int:
    """Read ``ASTEROID_LAB_MINERS_PER_ROUTE_OUT`` from Django settings (default 12)."""

    from django.conf import settings

    raw = getattr(settings, "ASTEROID_LAB_MINERS_PER_ROUTE_OUT", DEFAULT_MINERS_PER_SHAPE_ROUTE)
    value = int(raw)
    if value < 1:
        msg = "ASTEROID_LAB_MINERS_PER_ROUTE_OUT must be >= 1"
        raise ValueError(msg)
    return value
