"""Rotation helpers for canonical-E gene templates (genetic sample; not solver runtime)."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_DIRECTION_CW_ORDER: tuple[Direction, ...] = (
    Direction.E,
    Direction.S,
    Direction.W,
    Direction.N,
)


def steps_from_canonical_e(target: Direction) -> int:
    try:
        return _DIRECTION_CW_ORDER.index(target)
    except ValueError as exc:
        msg = f"unsupported direction: {target!r}"
        raise ValueError(msg) from exc


def rotate_offset(offset: Coord, steps: int) -> Coord:
    x, y = offset
    for _ in range(steps % 4):
        x, y = y, -x
    return (x, y)


def rotate_direction(direction: Direction, steps: int) -> Direction:
    idx = _DIRECTION_CW_ORDER.index(direction)
    return _DIRECTION_CW_ORDER[(idx + steps) % 4]


__all__ = ["rotate_direction", "rotate_offset", "steps_from_canonical_e"]
