"""Space Lift inner-source void egress routing."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04SourceView,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    RouteGoal,
    RouteGoalKind,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    TransportKind,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.space_lift_routing import (  # noqa: E501
    INNER_LIFT_SOURCE_PLACEMENT_PREFIX,
    astar_inner_source_via_space_lift,
    connector_reachable_void_cells,
    is_inner_lift_source,
    lift_void_egress_for_stub,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import make_complete_map


def test_is_inner_lift_source_prefix() -> None:
    assert is_inner_lift_source(f"{INNER_LIFT_SOURCE_PLACEMENT_PREFIX}0001")
    assert not is_inner_lift_source("rim-001")


def test_lift_void_egress_picks_connector_reachable_void() -> None:
    field = frozenset({(1, 1), (2, 1)})
    void = frozenset({(0, 1), (3, 1), (4, 1)})
    complete = make_complete_map(field_cells=field, external_void_cells=void | field)
    connector_voids = frozenset({(4, 1)})
    reachable = connector_reachable_void_cells(
        complete_map=complete,
        connector_void_coords=connector_voids,
    )
    assert reachable == frozenset({(3, 1), (4, 1)})
    egress = lift_void_egress_for_stub(
        stub=(2, 1),
        complete_map=complete,
        connector_void_coords=connector_voids,
    )
    assert egress == (3, 1)


def test_astar_inner_source_via_space_lift_reaches_connector() -> None:
    field = frozenset({(1, 1), (2, 1)})
    void = frozenset({(0, 1), (3, 1), (4, 1), (5, 1)})
    complete = make_complete_map(field_cells=field, external_void_cells=void | field)
    connector = (5, 1)
    goals = (
        RouteGoal(
            goal_id="c0",
            kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
            coord=connector,
            transport_kind=TransportKind.SHAPE_BELT,
            priority=0,
            connector_role=ExteriorConnectorRole.REQUIRED,
        ),
    )
    source = Layer04SourceView(
        placement_id=f"{INNER_LIFT_SOURCE_PLACEMENT_PREFIX}0001",
        m_output_stub=(2, 1),
        source_load_m=1,
        throughput_factor=4,
        equipment_cells=frozenset({(1, 1), (2, 1)}),
        route_probe_path=(),
    )
    result = astar_inner_source_via_space_lift(
        source=source,
        complete_map=complete,
        connector_void_coords=frozenset({connector}),
        goals=goals,
    )
    assert result is not None
    assert result.path[0] == (2, 1)
    assert result.goal_coord == connector
