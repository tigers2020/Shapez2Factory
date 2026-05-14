"""
Grid stepping and invariants for blueprint coordinates.

Wraps project cardinal-step rules without importing v1 layout code. Actual neighbor
logic may delegate to ``shapez_asteroid.extraction.shapez_grid`` in a later phase
after explicit review (keep this module thin).
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    Coord,
    as_blueprint_cell,
)


def assert_nonzero_x(x: int) -> None:
    """Blueprint invariant: column x==0 does not exist."""
    if x == 0:
        msg = "illegal blueprint x==0"
        raise ValueError(msg)


def manhattan(a: Coord | tuple[int, int], b: Coord | tuple[int, int]) -> int:
    """|ax-bx|+|ay-by| (diagonal moves not used for this helper)."""
    ax, ay = as_blueprint_cell(a)
    bx, by = as_blueprint_cell(b)
    return abs(ax - bx) + abs(ay - by)
