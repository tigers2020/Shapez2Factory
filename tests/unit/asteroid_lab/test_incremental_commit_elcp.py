"""ELCP Task 4 — incremental_commit hook and None-plan fallback."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput, RttpSkeletonConfig
from django_apps.asteroid_lab.optimization.routing.exterior_lane_capacity_planner import (
    build_exterior_lane_capacity_plan,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


@pytest.mark.django_db
def test_incremental_commit_without_lane_plan_unchanged_shape(
    greenfield_optimization_input: OptimizationInput,
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = initial_commit_domain(skeleton, inp)
    result_none = incremental_commit(
        PlacementGenome(commit_order=()),
        {},
        inp,
        skeleton,
        domain=domain,
        exterior_lane_plan=None,
    )
    assert result_none.exterior_lane_assignments == ()
    assert result_none.exterior_lane_assignment_state == ()


@pytest.mark.django_db
def test_incremental_commit_with_lane_plan_records_assignments_when_commits(
    greenfield_optimization_input: OptimizationInput,
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    inp = greenfield_optimization_input
    plan = build_exterior_lane_capacity_plan(
        inp,
        max_asteroid_throughput_per_min=Decimal("5760"),
        transport_kind=inp.transport_kind,
    )
    assert plan.required_lane_count >= 1
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=()),
        {},
        inp,
        skeleton,
        domain=domain,
        exterior_lane_plan=plan,
        resource_kind="shape",
    )
    assert result.exterior_lane_assignment_state
    assert len(result.exterior_lane_assignment_state) == len(plan.lanes)
