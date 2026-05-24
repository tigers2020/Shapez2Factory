"""Public catalog footprint rotation/translate (Track D+)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import BuildingFootprintCell
from django_apps.asteroid_lab.optimization.coords import Coord


class CatalogTransformError(ValueError):
    """Footprint could not be transformed."""


# E=+x, N=-y, S=+y, W=-x — matches pattern_library _rotation_matrix convention.
_UNIT_VECTOR: dict[CardinalDirection, Coord] = {
    CardinalDirection.E: (1, 0),
    CardinalDirection.N: (0, -1),
    CardinalDirection.S: (0, 1),
    CardinalDirection.W: (-1, 0),
}

_TILE_TO_CARDINAL: dict[str, CardinalDirection] = {
    "east": CardinalDirection.E,
    "north": CardinalDirection.N,
    "south": CardinalDirection.S,
    "west": CardinalDirection.W,
}


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


def tile_direction_to_cardinal(tile_direction: str) -> CardinalDirection:
    key = tile_direction.strip().lower()
    try:
        return _TILE_TO_CARDINAL[key]
    except KeyError as exc:
        raise CatalogTransformError(f"unsupported tile_direction {tile_direction!r}") from exc


def rotate_cardinal_direction(
    direction: CardinalDirection,
    rotation: CardinalDirection,
) -> CardinalDirection:
    order = (
        CardinalDirection.E,
        CardinalDirection.N,
        CardinalDirection.S,
        CardinalDirection.W,
    )
    idx = order.index(direction)
    rot_idx = order.index(rotation)
    return order[(idx + rot_idx) % 4]


def rotate_coord(rotation: CardinalDirection, point: Coord) -> Coord:
    return _rotate_point(rotation, point)


def cardinal_unit_vector(direction: CardinalDirection) -> Coord:
    return _UNIT_VECTOR[direction]


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


__all__ = [
    "CatalogTransformError",
    "cardinal_unit_vector",
    "expected_footprint_coords",
    "rotate_cardinal_direction",
    "rotate_coord",
    "tile_direction_to_cardinal",
]
