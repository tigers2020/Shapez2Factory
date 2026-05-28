"""ExteriorConnectionPlan builder and wire tests."""

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionShortfallReason,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.layout_t import (
    default_exterior_connector_layout_t,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.plan import (
    build_exterior_connection_plan,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.rotation import (
    FIELDWARD_ROTATION_BY_EDGE,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)


@pytest.mark.django_db
def test_required_connectors_uses_evtc_ceildiv_shape() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=100,
        speed_tier=1,
    )
    assert plan.unmet_reason is None
    assert len(plan.planned_connectors) == plan.reference_connector_count
    assert plan.reference_connector_count >= plan.required_connector_count
    assert plan.required_connector_count >= 1


@pytest.mark.django_db
def test_insufficient_slots_fail_closed() -> None:
    cm = build_rect_field_with_void_shell(width=2, height=2, void_pad=3)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("999999"),
        throughput_target_percent=100,
        speed_tier=1,
    )
    assert plan.unmet_reason == ExteriorConnectionShortfallReason.NO_FEASIBLE_CONNECTOR_SITES
    assert plan.planned_connectors == ()


@pytest.mark.django_db
def test_planned_connector_snapshot_fields() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("5000"),
        throughput_target_percent=50,
        speed_tier=1,
    )
    assert plan.planned_connectors
    row = plan.planned_connectors[0]
    assert row.connector_id.startswith("ext_conn_")
    assert row.coords == (row.void_coord,)
    assert row.layout_t == "SpaceBelt_Forward"
    assert 0 <= row.rotation <= 3


@pytest.mark.django_db
def test_wire_uses_lowercase_edge_slug() -> None:
    cm = build_rect_field_with_void_shell(width=8, height=8, void_pad=10)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("3000"),
        throughput_target_percent=100,
        speed_tier=1,
    )
    wire = exterior_connector_plan_to_metrics_dict(plan)["exterior_connector_plan"]
    assert isinstance(wire, dict)
    assert wire["version"] == "exterior_connector_plan.v2"
    connectors = wire.get("planned_connectors")
    assert isinstance(connectors, list) and connectors
    assert connectors[0]["edge"] in {"north", "east", "south", "west"}
    assert connectors[0]["role"] in {"required", "spare"}


def test_layout_t_and_rotation_are_separate() -> None:
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.EAST] == 2
    assert default_exterior_connector_layout_t(resource_kind="shape") == "SpaceBelt_Forward"
