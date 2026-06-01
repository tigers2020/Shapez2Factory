"""Sprite projection from committed paths (PR-L4-4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
    SpaceTransportTileCatalog,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    CommittedRoute,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.sprite_projector import (  # noqa: E501
    project_routes_to_tiles,
)

_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "asteroid_lab"
    / "space_transport_catalog_min.json"
)


@pytest.fixture
def catalog() -> SpaceTransportTileCatalog:
    return SpaceTransportTileCatalog.from_file(_FIXTURE)


def test_left_turn_west_to_north_resolves_left_turn(catalog: SpaceTransportTileCatalog) -> None:
    route = CommittedRoute(
        route_id="route_p0",
        placement_id="p0",
        path_coords=((0, 0), (1, 0), (1, -1)),
        group_id="conn_c0",
        route_cost=3,
    )
    tiles = project_routes_to_tiles(
        routes=(route,),
        transport_kind="space_belt",
        catalog=catalog,
    )
    corner = next(t for t in tiles if t.coord == (1, 0))
    assert corner.tile_id == "SpaceBelt_LeftTurn"


def test_straight_west_to_east_resolves_forward(catalog: SpaceTransportTileCatalog) -> None:
    route = CommittedRoute(
        route_id="route_p0",
        placement_id="p0",
        path_coords=((-1, 0), (0, 0), (1, 0)),
        group_id="conn_c0",
        route_cost=3,
    )
    tiles = project_routes_to_tiles(
        routes=(route,),
        transport_kind="space_belt",
        catalog=catalog,
    )
    mid = next(t for t in tiles if t.coord == (0, 0))
    assert mid.tile_id == "SpaceBelt_Forward"
    assert mid.input_dirs == ("W",)
    assert mid.output_dirs == ("E",)
