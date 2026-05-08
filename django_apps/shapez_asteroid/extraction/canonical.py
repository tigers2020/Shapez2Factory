"""Rotation-minimal fingerprint for clustered 1×1 footprints (STEP2 canonicalization)."""

from __future__ import annotations

Coord = tuple[int, int]


def _rotate_cells(cells: set[Coord], steps: int) -> set[Coord]:
    """CCW quartile rotation around origin."""

    pts = cells
    for _ in range(steps % 4):
        pts = {(-dy, dx) for (dx, dy) in pts}
    return pts


def canonicalize_cluster(*, cells: frozenset[Coord], anchor: Coord) -> frozenset[Coord]:
    """Translate ``anchor`` to origin, normalize by minimum rotation lex order on sorted coords."""

    ax, ay = anchor
    rel = frozenset((x - ax, y - ay) for x, y in cells)
    best: frozenset[Coord] | None = None
    for rot in range(4):
        trial = frozenset(_rotate_cells(set(rel), rot))
        if best is None or tuple(sorted(trial)) < tuple(sorted(best)):
            best = trial
    assert best is not None
    return best
