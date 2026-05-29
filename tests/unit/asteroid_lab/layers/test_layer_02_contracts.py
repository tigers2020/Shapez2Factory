"""Layer 02 exterior connector contract DTOs."""

from decimal import Decimal

from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnector,
)
from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)


def test_cardinal_edge_wire_slugs() -> None:
    assert CardinalEdge.NORTH.value == "north"
    assert CardinalEdge.EAST.value == "east"


def test_exterior_connector_role_wire_slugs() -> None:
    assert ExteriorConnectorRole.REQUIRED.value == "required"
    assert ExteriorConnectorRole.SPARE.value == "spare"


def test_exterior_connector_coords_singleton() -> None:
    conn = ExteriorConnector(
        connector_id="ext_conn_00",
        void_coord=(5, -6),
        edge=CardinalEdge.NORTH,
        layout_t="SpaceBelt_Forward",
        rotation=1,
        capacity_per_min=Decimal("1"),
        coords=((5, -6),),
        role=ExteriorConnectorRole.REQUIRED,
    )
    assert conn.coords == (conn.void_coord,)


def test_exterior_connector_requires_role() -> None:
    conn = ExteriorConnector(
        connector_id="ext_conn_00",
        void_coord=(1, -5),
        edge=CardinalEdge.NORTH,
        layout_t="SpaceBelt_Forward",
        rotation=1,
        capacity_per_min=Decimal("8640"),
        coords=((1, -5),),
        role=ExteriorConnectorRole.REQUIRED,
    )
    assert conn.role is ExteriorConnectorRole.REQUIRED


def test_exterior_connection_plan_reference_and_spare_counts() -> None:
    plan = ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        planning_target_per_min=Decimal("5000"),
        per_connector_capacity_per_min=Decimal("1000"),
        required_connector_count=5,
        reference_connector_count=10,
        spare_connector_count=5,
        planned_connectors=(),
        unmet_reason=None,
    )
    assert plan.reference_connector_count == 10
    assert plan.spare_connector_count == 5


def test_exterior_connection_plan_default_rules() -> None:
    plan = ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("100"),
        planning_target_per_min=Decimal("80"),
        per_connector_capacity_per_min=Decimal("1"),
        required_connector_count=0,
        reference_connector_count=0,
        spare_connector_count=0,
        planned_connectors=(),
        unmet_reason=None,
    )
    assert plan.slot_rule == "VOID_DEEP_SLOTS_V1"
    assert plan.placement_rule == "EDGE_WEIGHTED_EVEN_SPACING_V1"
    assert plan.rotation_rule == "FIELDWARD_FACING_V1"
