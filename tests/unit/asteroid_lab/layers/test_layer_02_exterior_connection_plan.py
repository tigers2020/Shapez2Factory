"""ExteriorConnectionPlan builder and wire tests."""

from decimal import Decimal

import pytest

from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionShortfallReason,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport import (
    plan as plan_mod,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.layout_t import (
    default_exterior_connector_layout_t,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.plan import (
    build_exterior_connection_plan,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.rotation import (
    FIELDWARD_ROTATION_BY_EDGE,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)
from tests.unit.asteroid_lab.layers.helpers.l02_rules import snapshot_rules_for_test


@pytest.mark.django_db
def test_required_connectors_uses_evtc_ceildiv_shape() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=100,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    assert plan.unmet_reason is None
    assert len(plan.planned_connectors) == plan.reference_connector_count
    assert plan.reference_connector_count >= plan.required_connector_count
    assert plan.required_connector_count >= 1


@pytest.mark.django_db
def test_zero_candidate_slots_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    cm = build_rect_field_with_void_shell(width=2, height=2, void_pad=3)
    monkeypatch.setattr(
        plan_mod,
        "build_exterior_lane_slots_by_edge",
        lambda _cm, **kwargs: {
            CardinalEdge.NORTH: [],
            CardinalEdge.EAST: [],
            CardinalEdge.SOUTH: [],
            CardinalEdge.WEST: [],
        },
    )
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("999999"),
        throughput_target_percent=100,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    assert plan.unmet_reason == ExteriorConnectionShortfallReason.NO_FEASIBLE_CONNECTOR_SITES
    assert plan.planned_connectors == ()
    assert plan.required_connector_count > 0


@pytest.mark.django_db
def test_insufficient_slots_places_partial_required(monkeypatch: pytest.MonkeyPatch) -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    fake_slots = {
        CardinalEdge.NORTH: [(0, -12), (1, -12), (2, -12)],
        CardinalEdge.EAST: [(22, 5), (22, 6)],
        CardinalEdge.SOUTH: [],
        CardinalEdge.WEST: [],
    }
    monkeypatch.setattr(
        plan_mod,
        "build_exterior_lane_slots_by_edge",
        lambda _cm, **kwargs: fake_slots,
    )
    total_slots = 5
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("999999"),
        throughput_target_percent=100,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    required_planned = sum(
        1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.REQUIRED
    )
    assert plan.required_connector_count > total_slots
    assert plan.unmet_reason == ExteriorConnectionShortfallReason.INSUFFICIENT_CONNECTOR_SITES
    assert required_planned == total_slots
    assert len(plan.planned_connectors) == total_slots


@pytest.mark.django_db
def test_planned_connector_snapshot_fields() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("5000"),
        throughput_target_percent=50,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    assert plan.planned_connectors
    row = plan.planned_connectors[0]
    assert row.connector_id.startswith("ext_conn_")
    assert row.coords == (row.void_coord,)
    assert row.layout_t == "SpaceBelt_Forward"
    assert 0 <= row.rotation <= 3


@pytest.mark.django_db
def test_wire_includes_shortfall_metrics_when_insufficient_slots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    fake_slots = {
        CardinalEdge.NORTH: [(0, -12), (1, -12)],
        CardinalEdge.EAST: [(22, 5)],
        CardinalEdge.SOUTH: [],
        CardinalEdge.WEST: [],
    }
    monkeypatch.setattr(
        plan_mod,
        "build_exterior_lane_slots_by_edge",
        lambda _cm, **kwargs: fake_slots,
    )
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("999999"),
        throughput_target_percent=100,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    wire = exterior_connector_plan_to_metrics_dict(plan)["exterior_connector_plan"]
    assert wire["unmet_reason"] == "insufficient_connector_sites"
    assert wire["candidate_slot_count"] == 3
    assert wire["connector_shortfall_count"] == plan.required_connector_count - 3
    assert wire["required_planned_count"] == 3


@pytest.mark.django_db
def test_wire_uses_lowercase_edge_slug() -> None:
    cm = build_rect_field_with_void_shell(width=8, height=8, void_pad=10)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("3000"),
        throughput_target_percent=100,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
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
