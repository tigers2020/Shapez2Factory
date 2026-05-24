"""Public catalog footprint rotation/translate (Track D+)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import BuildingFootprintCell
from django_apps.asteroid_lab.optimization.coords import Coord


class CatalogTransformError(ValueError):
    """Footprint could not be transformed."""


def _rotation_matrix(direction: CardinalDirection) -> tuple[tuple[int, int], tuple[int, int]]:
    if direction == CardinalDirection.E:
        return ((1, 0), (0, 1))
    if direction == CardinalDirection.N:
        return ((0, 1), (-1, 0))
    if direction == CardinalDirection.S:
        return ((0, -1), (1, 0))
    if direction == CardinalDirection.W:
        return ((-1, 0), (0, -1))
    raise CatalogTransformError(f"unsupported rotation {direction!r}")


def _rotate_point(direction: CardinalDirection, point: Coord) -> Coord:
    (a11, a12), (a21, a22) = _rotation_matrix(direction)
    return (a11 * point[0] + a12 * point[1], a21 * point[0] + a22 * point[1])


def expected_footprint_coords(
    footprint_cells: tuple[BuildingFootprintCell, ...],
    *,
    anchor_coord: Coord,
    rotation: CardinalDirection,
) -> frozenset[Coord]:
    if not footprint_cells:
        raise CatalogTransformError("empty footprint_cells")
    out: set[Coord] = set()
    for cell in footprint_cells:
        local: Coord = (cell.x, cell.y)
        rotated = _rotate_point(rotation, local)
        out.add((anchor_coord[0] + rotated[0], anchor_coord[1] + rotated[1]))
    return frozenset(out)


__all__ = ["CatalogTransformError", "expected_footprint_coords"]
