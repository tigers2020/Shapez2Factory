"""Capacity planner tests (Solver Runtime PR2.5)."""

from __future__ import annotations

import math

from django_apps.asteroid_lab.optimization.capacity_planner import (
    DEFAULT_MINEABLE_PACKING_EFFICIENCY,
    FLUID_PLATFORMS_PER_GOAL,
    PLATFORM_FOOTPRINT_CELLS,
    plan_capacity,
)


def test_capacity_planner_estimates_extractor_groups_with_packing() -> None:
    plan = plan_capacity(mineable_cell_count=60)
    assert plan.platform_footprint_cells == PLATFORM_FOOTPRINT_CELLS
    assert plan.packing_efficiency == DEFAULT_MINEABLE_PACKING_EFFICIENCY
    assert plan.estimated_extractor_groups == int(
        math.floor(60 * DEFAULT_MINEABLE_PACKING_EFFICIENCY / PLATFORM_FOOTPRINT_CELLS)
    )
    assert plan.estimated_extractor_groups == 9
    assert plan.shape_goal_count == 2  # min(8, max(2, min(ceil(9/12), 18)))


def test_capacity_planner_estimates_shape_goal_count_by_12() -> None:
    plan = plan_capacity(mineable_cell_count=100)
    assert plan.estimated_extractor_groups == 15
    assert plan.shape_goal_count == 2

    single = plan_capacity(mineable_cell_count=80)
    assert single.estimated_extractor_groups == 12
    assert single.shape_goal_count == 2


def test_capacity_shape_goals_capped_by_extractor_scale() -> None:
    plan = plan_capacity(mineable_cell_count=600)
    assert plan.estimated_extractor_groups == 90
    assert plan.shape_goal_count == 8


def test_capacity_planner_estimates_fluid_goal_count_by_72() -> None:
    plan = plan_capacity(mineable_cell_count=360, fluid_platform_count=144)
    assert plan.estimated_extractor_groups == 54
    assert plan.fluid_goal_count == math.ceil(144 / FLUID_PLATFORMS_PER_GOAL)
    assert plan.fluid_goal_count == 2
