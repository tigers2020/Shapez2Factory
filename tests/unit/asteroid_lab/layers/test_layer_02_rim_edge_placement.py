"""Exterior lane connector placement (L2 UI edge picker contract)."""

from decimal import Decimal

import pytest

from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.plan import (
    build_exterior_connection_plan,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.slots import (
    CONNECTOR_LANE_SPACING,
    EXTERIOR_LANE_OFFSET,
    build_exterior_lane_slots_by_edge,
    parse_allowed_cardinal_edges,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    make_complete_map,
)
from tests.unit.asteroid_lab.layers.helpers.l02_rules import snapshot_rules_for_test


def _symmetric_field_map(*, half_extent: int) -> object:
    field = frozenset(
        (x, y)
        for x in range(-half_extent, half_extent + 1)
        for y in range(-half_extent, half_extent + 1)
    )
    return make_complete_map(field_cells=field, external_void_cells=frozenset())


def test_exterior_lane_east_coords_for_13_half_extent_map() -> None:
    cm = _symmetric_field_map(half_extent=13)
    east = build_exterior_lane_slots_by_edge(cm, allowed_edges=frozenset({CardinalEdge.EAST}))[
        CardinalEdge.EAST
    ]
    assert east[:4] == [(25, 25), (23, 25), (21, 25), (19, 25)]


def test_exterior_lane_other_edges_are_corner_mirrors() -> None:
    cm = _symmetric_field_map(half_extent=13)
    lanes = build_exterior_lane_slots_by_edge(cm)
    assert lanes[CardinalEdge.NORTH][:4] == [(-25, -25), (-23, -25), (-21, -25), (-19, -25)]
    assert lanes[CardinalEdge.WEST][:4] == [(-25, 25), (-25, 23), (-25, 21), (-25, 19)]
    assert lanes[CardinalEdge.SOUTH][:4] == [(25, -25), (23, -25), (21, -25), (19, -25)]


def test_exterior_lane_spacing_and_offset_constants() -> None:
    assert EXTERIOR_LANE_OFFSET == 12
    assert CONNECTOR_LANE_SPACING == 2


def test_parse_allowed_cardinal_edges_defaults_to_all() -> None:
    assert len(parse_allowed_cardinal_edges(None)) == 4
    assert parse_allowed_cardinal_edges(["north", "bad", "EAST"]) == frozenset(
        {CardinalEdge.NORTH, CardinalEdge.EAST},
    )


@pytest.mark.django_db
def test_plan_places_connectors_only_on_selected_edges() -> None:
    cm = _symmetric_field_map(half_extent=13)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("1000"),
        throughput_target_percent=100,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
        allowed_connector_edges=frozenset({CardinalEdge.EAST, CardinalEdge.WEST}),
    )
    assert plan.planned_connectors
    assert {connector.edge for connector in plan.planned_connectors}.issubset(
        {CardinalEdge.EAST, CardinalEdge.WEST},
    )


@pytest.mark.django_db
def test_plan_east_required_connectors_use_lane_coords() -> None:
    cm = _symmetric_field_map(half_extent=13)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("999999"),
        throughput_target_percent=100,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
        allowed_connector_edges=frozenset({CardinalEdge.EAST}),
    )
    required = [
        connector.void_coord
        for connector in plan.planned_connectors
        if connector.role is ExteriorConnectorRole.REQUIRED
    ]
    assert required[:4] == [(25, 25), (23, 25), (21, 25), (19, 25)]
