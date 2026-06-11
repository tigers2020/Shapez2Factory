"""Layer 04 A* search (PR-L4-2)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    RouteGoal,
    RouteGoalKind,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import TransportKind
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.astar import (
    astar_to_nearest_goal,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.route_domain import (  # noqa: E501
    build_l4_route_search_domain,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
    make_complete_map,
)


def test_astar_prefers_void_over_field() -> None:
    # Field block at y=1,x=1..2; void corridor along y=0 and y=2.
    field = frozenset({(1, 1), (2, 1)})
    void = frozenset({(0, 0), (1, 0), (2, 0), (3, 0), (0, 2), (1, 2), (2, 2), (3, 2), (3, 1)})
    cm = make_complete_map(field_cells=field, external_void_cells=void)
    domain = build_l4_route_search_domain(
        complete_map=cm,
        miner_cells=frozenset(),
        extension_cells=frozenset(),
    )
    goal = RouteGoal(
        goal_id="g0",
        kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
        coord=(3, 0),
        transport_kind=TransportKind.SPACE_BELT,
        priority=0,
        connector_role=ExteriorConnectorRole.REQUIRED,
    )
    result = astar_to_nearest_goal(domain=domain, start=(0, 0), goals=(goal,))
    assert result is not None
    interior = set(result.path[1:-1])
    assert field.isdisjoint(interior)


def test_astar_reaches_connector_on_larger_map() -> None:
    cm = build_rect_field_with_void_shell(width=6, height=6, void_pad=3)
    domain = build_l4_route_search_domain(
        complete_map=cm,
        miner_cells=frozenset(),
        extension_cells=frozenset(),
    )
    goal_coord = (-1, 3)
    assert goal_coord in cm.external_void_cells
    goal = RouteGoal(
        goal_id="ext",
        kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
        coord=goal_coord,
        transport_kind=TransportKind.SPACE_BELT,
        priority=0,
        connector_role=ExteriorConnectorRole.REQUIRED,
    )
    start = (2, 3)
    result = astar_to_nearest_goal(domain=domain, start=start, goals=(goal,))
    assert result is not None
    assert result.path[0] == start
    assert result.path[-1] == goal_coord
