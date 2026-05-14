"""v2 layering: ``coord`` = atomic rules; ``grid`` = bbox / neighbor sets / tuple steps."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    Coord,
    is_physical_coord,
    neighbor,
    step_x,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.grid import (
    cardinal_neighbors4,
    iter_physical_bbox_cells,
    iter_physical_bbox_coords,
    iter_physical_x_in_range,
    step_blueprint_cell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.routing.connectivity import (
    flood_reachable,
    neighbors4,
)


def test_step_x_seam_hops() -> None:
    assert step_x(1, -1) == -1
    assert step_x(-1, 1) == 1
    assert step_x(2, -1) == 1
    assert step_x(-2, 1) == -1


def test_neighbor_matches_seam_west_east() -> None:
    assert neighbor(Coord(1, 7), (-1, 0)) == Coord(-1, 7)
    assert neighbor(Coord(-1, 7), (1, 0)) == Coord(1, 7)


def test_step_blueprint_cell_delegates_to_neighbor() -> None:
    assert step_blueprint_cell((1, 7), (-1, 0)) == (-1, 7)
    assert step_blueprint_cell((-1, 7), (1, 0)) == (1, 7)


def test_is_physical_coord() -> None:
    assert is_physical_coord(Coord(1, 0))
    assert not is_physical_coord(Coord(0, 0))


def test_cardinal_neighbors_exclude_x_zero() -> None:
    n = cardinal_neighbors4((1, 0))
    assert all(c[0] != 0 for c in n)
    assert (-1, 0) in n
    assert (1, 1) in n and (1, -1) in n


def test_neighbors4_matches_grid_policy() -> None:
    assert neighbors4((1, 0)) == cardinal_neighbors4((1, 0))


def test_iter_physical_x_skips_zero() -> None:
    assert list(iter_physical_x_in_range(-1, 1)) == [-1, 1]
    assert list(iter_physical_x_in_range(0, 0)) == []


def test_iter_physical_bbox_coords_and_cells_skips_x_zero() -> None:
    b = BBox(min_x=-1, min_y=0, max_x=1, max_y=0)
    coords = list(iter_physical_bbox_coords(b))
    assert coords == [Coord(-1, 0), Coord(1, 0)]
    cells = list(iter_physical_bbox_cells(b))
    assert cells == [(-1, 0), (1, 0)]


def test_flood_reachable_across_seam_without_x_zero() -> None:
    p = frozenset({(-1, 0), (1, 0)})
    r = flood_reachable((1, 0), p)
    assert r == p
