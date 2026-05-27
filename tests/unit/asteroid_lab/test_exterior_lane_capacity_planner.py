"""ELCP Task 2 — exterior lane capacity plan builder."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.routing.exterior_lane_capacity_planner import (
    build_exterior_lane_capacity_plan,
)
from django_apps.asteroid_lab.services.required_external_connectors import (
    required_external_connectors,
)


@pytest.mark.django_db
def test_build_plan_lane_count_matches_required_connectors(
    greenfield_optimization_input: OptimizationInput,
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    inp = greenfield_optimization_input
    max_throughput = Decimal("5760")
    plan = build_exterior_lane_capacity_plan(
        inp,
        max_asteroid_throughput_per_min=max_throughput,
        transport_kind=inp.transport_kind,
    )
    expected_required = required_external_connectors(
        max_asteroid_throughput_per_min=max_throughput,
        transport_kind=inp.transport_kind,
    )
    assert plan.required_lane_count == expected_required
    assert len(plan.lanes) == expected_required
    assert plan.lanes[0].lane_id == "exterior_lane:shape_belt:0"
    assert plan.lanes[0].connector_goal.goal_kind == RouteGoalKind.EXTERNAL_MARGIN
    assert sum(lane.target_load_per_min for lane in plan.lanes) >= max_throughput
    for lane in plan.lanes:
        assert lane.connector_goal.coord in inp.external_void_cells
        assert lane.anchor_coord == lane.connector_goal.coord


@pytest.mark.django_db
def test_build_plan_zero_required_returns_empty_lanes(
    greenfield_optimization_input: OptimizationInput,
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    inp = greenfield_optimization_input
    plan = build_exterior_lane_capacity_plan(
        inp,
        max_asteroid_throughput_per_min=Decimal("0"),
        transport_kind=inp.transport_kind,
    )
    assert plan.required_lane_count == 0
    assert plan.lanes == ()
