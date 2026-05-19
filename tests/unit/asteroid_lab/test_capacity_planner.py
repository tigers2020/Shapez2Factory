"""Capacity planner tests (Solver Runtime PR2.5)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.capacity_planner import plan_capacity


def test_capacity_planner_estimates_shape_goal_count_by_12() -> None:
    plan = plan_capacity(
        mineable_cell_count=60,
        shape_platform_count=24,
        fluid_platform_count=0,
    )
    assert plan.shape_goal_count == 2
    assert plan.estimated_max_samples == 12

    single = plan_capacity(
        mineable_cell_count=60,
        shape_platform_count=12,
        fluid_platform_count=0,
    )
    assert single.shape_goal_count == 1


def test_capacity_planner_estimates_fluid_goal_count_by_72() -> None:
    plan = plan_capacity(
        mineable_cell_count=360,
        shape_platform_count=0,
        fluid_platform_count=144,
    )
    assert plan.fluid_goal_count == 2
    assert plan.estimated_max_samples == 72
