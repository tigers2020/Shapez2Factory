"""Tagged coordinate frame types (PR-A — no runtime behavior change elsewhere)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.snapshots.coord_frames import (
    CoordFrame,
    IslandRawCoord,
    ServerCoord,
    WorldRawCoord,
    island_to_tuple,
    neighbors4_island,
    server_coord_to_tuple,
)
from django_apps.asteroid_lab.snapshots.grid_contract import neighbors4, neighbors4_server


def test_coord_frame_enum_values_reserved() -> None:
    assert CoordFrame.SERVER_DENSE.value == "server_dense"
    assert CoordFrame.ISLAND_RAW.value == "island_raw"
    assert CoordFrame.WORLD_RAW.value == "world_raw"


def test_world_raw_rejects_x_zero() -> None:
    with pytest.raises(ValueError, match="x == 0"):
        WorldRawCoord(0, 1)


def test_island_raw_allows_x_zero() -> None:
    assert IslandRawCoord(0, 1).x == 0


def test_server_coord_allows_x_zero() -> None:
    assert ServerCoord(0, 1).x == 0


def test_neighbors4_island_standard_grid() -> None:
    c = IslandRawCoord(1, 2)
    nbrs = neighbors4_island(c)
    assert nbrs == (
        IslandRawCoord(0, 2),
        IslandRawCoord(2, 2),
        IslandRawCoord(1, 1),
        IslandRawCoord(1, 3),
    )


def test_tuple_conversion_helpers() -> None:
    assert island_to_tuple(IslandRawCoord(-1, 0)) == (-1, 0)
    assert server_coord_to_tuple(ServerCoord(3, 4)) == (3, 4)


def test_neighbors4_server_is_deprecated_alias() -> None:
    c = (2, 3)
    assert neighbors4_server(c) == neighbors4(c)
