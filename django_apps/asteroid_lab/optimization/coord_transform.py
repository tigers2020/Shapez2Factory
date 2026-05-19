"""Rotation helpers for canonical-E gene templates (Server Coord, origin-relative)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import Direction

# Clockwise quarter-turn steps from canonical E: E=0, S=1, W=2, N=3.
_DIRECTION_CW_ORDER: tuple[Direction, ...] = (
    Direction.E,
    Direction.S,
    Direction.W,
    Direction.N,
)


def steps_from_canonical_e(target: Direction) -> int:
    """Quarter-turn CW steps so canonical E output faces ``target``."""

    try:
        return _DIRECTION_CW_ORDER.index(target)
    except ValueError as exc:
        msg = f"unsupported direction: {target!r}"
        raise ValueError(msg) from exc


def rotate_offset(offset: Coord, steps: int) -> Coord:
    """Rotate ``offset`` around origin by ``steps`` quarter-turns clockwise."""

    x, y = offset
    for _ in range(steps % 4):
        x, y = y, -x
    return (x, y)


def rotate_direction(direction: Direction, steps: int) -> Direction:
    """Rotate a cardinal direction by ``steps`` quarter-turns clockwise."""

    idx = _DIRECTION_CW_ORDER.index(direction)
    return _DIRECTION_CW_ORDER[(idx + steps) % 4]
