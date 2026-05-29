"""Layer 03 RouteGoal builder tests (PR-3a)."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnector,
)
from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from django_apps.asteroid_lab.layers.contracts.route_goal import (
    ROUTE_GOAL_PRIORITY_REQUIRED,
    ROUTE_GOAL_PRIORITY_SPARE,
    RouteGoalKind,
    build_layer03_route_goals,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind


def _plan_with_required_and_spare() -> ExteriorConnectionPlan:
    return ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        planning_target_per_min=Decimal("5000"),
        per_connector_capacity_per_min=Decimal("1000"),
        required_connector_count=1,
        reference_connector_count=2,
        spare_connector_count=1,
        planned_connectors=(
            ExteriorConnector(
                connector_id="ext_conn_spare",
                void_coord=(10, -6),
                edge=CardinalEdge.EAST,
                layout_t="SpaceBelt_Forward",
                rotation=2,
                capacity_per_min=Decimal("1000"),
                coords=((10, -6),),
                role=ExteriorConnectorRole.SPARE,
            ),
            ExteriorConnector(
                connector_id="ext_conn_required",
                void_coord=(5, -6),
                edge=CardinalEdge.NORTH,
                layout_t="SpaceBelt_Forward",
                rotation=1,
                capacity_per_min=Decimal("1000"),
                coords=((5, -6),),
                role=ExteriorConnectorRole.REQUIRED,
            ),
        ),
        unmet_reason=None,
    )


def test_build_layer03_route_goals_required_before_spare() -> None:
    plan = _plan_with_required_and_spare()
    goals = build_layer03_route_goals(plan, transport_kind=TransportKind.SHAPE_BELT)
    assert len(goals) == 2
    assert goals[0].priority == ROUTE_GOAL_PRIORITY_REQUIRED
    assert goals[0].goal_id == "ext_conn_required"
    assert goals[1].priority == ROUTE_GOAL_PRIORITY_SPARE
    assert goals[1].goal_id == "ext_conn_spare"
    assert goals[0].kind is RouteGoalKind.EXTERIOR_CONNECTOR_VOID


def test_build_layer03_route_goals_filters_by_transport_kind() -> None:
    plan = _plan_with_required_and_spare()
    pipe_plan = ExteriorConnectionPlan(
        transport_kind="fluid",
        terrain_upper_bound_per_min=Decimal("100"),
        planning_target_per_min=Decimal("80"),
        per_connector_capacity_per_min=Decimal("1"),
        required_connector_count=1,
        reference_connector_count=1,
        spare_connector_count=0,
        planned_connectors=(
            ExteriorConnector(
                connector_id="ext_conn_pipe",
                void_coord=(1, -5),
                edge=CardinalEdge.NORTH,
                layout_t="SpacePipe_Forward",
                rotation=1,
                capacity_per_min=Decimal("1"),
                coords=((1, -5),),
                role=ExteriorConnectorRole.REQUIRED,
            ),
        ),
        unmet_reason=None,
    )
    shape_goals = build_layer03_route_goals(plan, transport_kind=TransportKind.SHAPE_BELT)
    pipe_goals = build_layer03_route_goals(pipe_plan, transport_kind=TransportKind.FLUID_PIPE)
    assert len(shape_goals) == 2
    assert len(pipe_goals) == 1
    assert all(g.transport_kind == TransportKind.SHAPE_BELT for g in shape_goals)
    assert pipe_goals[0].transport_kind == TransportKind.FLUID_PIPE
