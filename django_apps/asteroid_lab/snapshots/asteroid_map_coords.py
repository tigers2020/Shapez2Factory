"""Shapez2 asteroid / lab map coordinates (world x has no zero column).

Invariant:
- Horizontal order: ..., -2, -1, 1, 2, 3, ... — there is no x == 0.
- The cell immediately to the right of (-1, y) is (1, y), not (0, y).
- UI anchor (1, 0) maps to visual column index 0 via ``visual_col``.

Used by transport BFS / equipment adjacency and must stay aligned with the Lab JS renderer.
"""

from __future__ import annotations

from collections.abc import Iterator

from django_apps.asteroid_lab.snapshots.coord_frames import WorldRawCoord

_MSG_NO_X0 = "Shapez2 asteroid grid has no x == 0 coordinate"


def visual_col(x: int) -> int:
    """Map world x (non-zero) to a dense visual column index (..., -1, 0, 1, ...)."""

    if x == 0:
        raise ValueError(_MSG_NO_X0)
    if x < 0:
        return x
    return x - 1


def left_of(x: int) -> int:
    if x == 0:
        raise ValueError(_MSG_NO_X0)
    if x == 1:
        return -1
    return x - 1


def right_of(x: int) -> int:
    if x == 0:
        raise ValueError(_MSG_NO_X0)
    if x == -1:
        return 1
    return x + 1


def iter_four_neighbors_map(
    x: int, y: int, layer: int | None
) -> Iterator[tuple[int, int, int | None]]:
    """Cardinal neighbors on the asteroid map (no x == 0 column).

    Order: east (right_of), west (left_of), south (y+1), north (y-1) — matches prior dx/dy order.

    Decoded blueprints may still carry a bogus ``x == 0`` row from upstream; do not raise — there
    is no valid neighbor step through the missing column, so yield nothing.
    """

    if x == 0:
        return
    yield (right_of(x), y, layer)
    yield (left_of(x), y, layer)
    yield (x, y + 1, layer)
    yield (x, y - 1, layer)


def world_raw_coord(x: int, y: int) -> WorldRawCoord:
    """Construct a world-map coordinate (rejects ``x == 0``)."""

    return WorldRawCoord(x, y)


def neighbors4_world(c: WorldRawCoord) -> tuple[WorldRawCoord, ...]:
    """Cardinal neighbors on the asteroid world map (no ``x == 0`` column)."""

    if c.x == 0:
        return ()
    out: list[WorldRawCoord] = []
    for nx, ny, _layer in iter_four_neighbors_map(c.x, c.y, None):
        out.append(WorldRawCoord(nx, ny))
    return tuple(out)
