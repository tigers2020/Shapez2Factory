"""Bundle selection target contract tests."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.bundle_selection_targets import (
    compute_bundle_selection_targets,
)
from django_apps.asteroid_lab.optimization.capacity_planner import (
    FLUID_PLATFORMS_PER_GOAL,
    SHAPE_PLATFORMS_PER_GOAL,
)
from django_apps.asteroid_lab.optimization.enums import RouteGoalKind, TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal


def _goal(
    coord: tuple[int, int],
    *,
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=transport_kind,
        priority=20,
        existing_trunk=False,
    )


def test_target_miner_bundle_count_seven_shape_goals() -> None:
    goals = frozenset(_goal((i, 0)) for i in range(7))
    targets = compute_bundle_selection_targets(goals, miners_per_shape_route=12)
    assert targets.route_out_count == 7
    assert targets.target_miner_bundle_count == 84
    assert targets.miners_per_shape_route == SHAPE_PLATFORMS_PER_GOAL


def test_target_miner_bundle_count_mixed_shape_and_fluid() -> None:
    goals = frozenset(
        {
            _goal((0, 0), transport_kind=TransportKind.SHAPE_BELT),
            _goal((1, 0), transport_kind=TransportKind.SHAPE_BELT),
            _goal((2, 0), transport_kind=TransportKind.FLUID_PIPE),
        }
    )
    targets = compute_bundle_selection_targets(goals, miners_per_shape_route=12)
    assert targets.route_out_count == 3
    assert targets.shape_route_out_count == 2
    assert targets.fluid_route_out_count == 1
    assert targets.target_miner_bundle_count == 12 + 12 + FLUID_PLATFORMS_PER_GOAL
