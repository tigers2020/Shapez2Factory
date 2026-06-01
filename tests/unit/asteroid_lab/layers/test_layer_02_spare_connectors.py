"""Layer 02 spare (reference@100%) connector placement."""

from decimal import Decimal

import pytest

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.plan import (
    build_exterior_connection_plan,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)
from tests.unit.asteroid_lab.layers.helpers.l02_rules import snapshot_rules_for_test


@pytest.mark.django_db
def test_spare_count_zero_when_target_percent_100() -> None:
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
    assert plan.spare_connector_count == 0
    assert plan.reference_connector_count == plan.required_connector_count
    assert all(c.role is ExteriorConnectorRole.REQUIRED for c in plan.planned_connectors)


@pytest.mark.django_db
def test_spare_positive_when_target_below_100() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=50,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    assert plan.unmet_reason is None
    assert plan.reference_connector_count > plan.required_connector_count
    assert plan.spare_connector_count == (
        plan.reference_connector_count - plan.required_connector_count
    )
    required_rows = [c for c in plan.planned_connectors if c.role is ExteriorConnectorRole.REQUIRED]
    spare_rows = [c for c in plan.planned_connectors if c.role is ExteriorConnectorRole.SPARE]
    assert len(required_rows) == plan.required_connector_count
    assert len(spare_rows) <= plan.spare_connector_count
    assert len(plan.planned_connectors) == len(required_rows) + len(spare_rows)


@pytest.mark.django_db
def test_required_and_spare_void_coords_disjoint() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=50,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    coords = [c.void_coord for c in plan.planned_connectors]
    assert len(coords) == len(set(coords))


@pytest.mark.django_db
def test_spare_connectors_are_not_adjacent_to_required_on_same_edge() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=50,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.slots import (
        build_candidate_slots_by_edge,
    )

    edge_slots = build_candidate_slots_by_edge(cm)
    edge_slot_indices = {
        edge: {coord: index for index, coord in enumerate(slots)}
        for edge, slots in edge_slots.items()
    }
    required_by_edge: dict = {}
    spare_by_edge: dict = {}
    for connector in plan.planned_connectors:
        bucket = (
            required_by_edge if connector.role is ExteriorConnectorRole.REQUIRED else spare_by_edge
        )
        bucket.setdefault(connector.edge, []).append(
            edge_slot_indices[connector.edge][connector.void_coord]
        )
    for edge, spare_indices in spare_by_edge.items():
        required_indices = required_by_edge.get(edge, [])
        if not required_indices:
            continue
        for spare_index in spare_indices:
            assert all(abs(spare_index - required_index) > 1 for required_index in required_indices)


@pytest.mark.django_db
def test_partial_spare_placement_is_success_when_required_slots_fit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
    from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport import (
        plan as plan_mod,
    )

    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    fake_slots = {
        CardinalEdge.NORTH: [(0, -12), (5, -12), (10, -12)],
        CardinalEdge.EAST: [(22, 5), (22, 10)],
        CardinalEdge.SOUTH: [],
        CardinalEdge.WEST: [],
    }
    monkeypatch.setattr(
        plan_mod,
        "build_candidate_slots_by_edge",
        lambda _cm: fake_slots,
    )
    total_slots = 5

    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("40000"),
        throughput_target_percent=50,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    required_planned = sum(
        1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.REQUIRED
    )
    spare_planned = sum(1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.SPARE)

    assert plan.unmet_reason is None
    assert plan.spare_connector_count > 0
    assert total_slots >= plan.required_connector_count
    assert total_slots < plan.reference_connector_count
    assert required_planned == plan.required_connector_count
    assert spare_planned < plan.spare_connector_count


@pytest.mark.django_db
def test_zero_target_places_only_spare_reference_markers() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=0,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    assert plan.unmet_reason is None
    assert plan.required_connector_count == 0
    assert plan.spare_connector_count == plan.reference_connector_count
    assert plan.planned_connectors
    assert all(c.role is ExteriorConnectorRole.SPARE for c in plan.planned_connectors)


@pytest.mark.django_db
def test_wire_v2_includes_role_and_reference_counts() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=50,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    wire = exterior_connector_plan_to_metrics_dict(plan)["exterior_connector_plan"]
    assert wire["version"] == "exterior_connector_plan.v2"
    assert wire["reference_connector_count"] == plan.reference_connector_count
    assert wire["spare_connector_count"] == plan.spare_connector_count
    required_planned = sum(
        1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.REQUIRED
    )
    spare_planned = sum(1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.SPARE)
    assert wire["required_planned_count"] == required_planned
    assert wire["spare_planned_count"] == spare_planned
    assert wire["planned_connector_count"] == required_planned + spare_planned
    assert wire["planned_connector_count"] == len(plan.planned_connectors)
    roles = {row["role"] for row in wire["planned_connectors"]}
    assert roles <= {"required", "spare"}
