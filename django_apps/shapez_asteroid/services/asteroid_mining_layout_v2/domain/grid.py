"""
Grid stepping and invariants for blueprint coordinates.

Wraps project cardinal-step rules without importing v1 layout code. Actual neighbor
logic may delegate to ``shapez_asteroid.extraction.shapez_grid`` in a later phase
after explicit review (keep this module thin).
"""

from __future__ import annotations


def assert_nonzero_x(x: int) -> None:
    """Blueprint invariant: column x==0 does not exist."""
    if x == 0:
        msg = "illegal blueprint x==0"
        raise ValueError(msg)


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    """|ax-bx|+|ay-by| (diagonal moves not used for this helper)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
