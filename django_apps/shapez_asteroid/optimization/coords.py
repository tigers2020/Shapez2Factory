"""Server dense grid coordinates (Phase 1 contract)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_asteroid.optimization.enums import CardinalDirection


@dataclass(frozen=True, slots=True)
class Coord:
    """Server X / Server Y on the integer dense grid (x may be 0)."""

    x: int
    y: int


@dataclass(frozen=True, slots=True)
class BBox:
    """Inclusive server-axis bounding box."""

    min_x: int
    max_x: int
    min_y: int
    max_y: int

    def iter_cells(self) -> tuple[Coord, ...]:
        out: list[Coord] = []
        for x in range(self.min_x, self.max_x + 1):
            for y in range(self.min_y, self.max_y + 1):
                out.append(Coord(x, y))
        return tuple(out)


def neighbors4_server(coord: Coord) -> tuple[Coord, ...]:
    """Standard cardinal ±1 adjacency on the dense server grid (includes x = 0)."""

    x, y = coord.x, coord.y
    return (
        Coord(x - 1, y),
        Coord(x + 1, y),
        Coord(x, y - 1),
        Coord(x, y + 1),
    )


def cardinal_unit_toward(src: Coord, dst: Coord) -> CardinalDirection:
    """One cardinal step toward ``dst`` (dominant axis; ties prefer X)."""

    dx = dst.x - src.x
    dy = dst.y - src.y
    if dx == 0 and dy == 0:
        raise ValueError("src and dst must differ for cardinal_unit_toward")
    if abs(dx) >= abs(dy):
        if dx > 0:
            return CardinalDirection.EAST
        if dx < 0:
            return CardinalDirection.WEST
    if dy > 0:
        return CardinalDirection.SOUTH
    if dy < 0:
        return CardinalDirection.NORTH
    return CardinalDirection.EAST
