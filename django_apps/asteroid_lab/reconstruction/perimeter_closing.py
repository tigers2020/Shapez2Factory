"""Perimeter morphology before external flood (diagonal closing + orthogonal slit seal)."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.grid import Coord, iter_bbox_cells
from django_apps.asteroid_lab.reconstruction.shell import _strict_bbox_interior_cells


def _touches_bbox_edge(c: Coord, w0: int, w1: int, h0: int, h1: int) -> bool:
    x, y = c
    return x <= w0 or x >= w1 or y <= h0 or y >= h1


def close_diagonal_leaks(
    solid: set[Coord],
    bbox_bounds: tuple[int, int, int, int],
) -> frozenset[Coord]:
    """Chebyshev 1-step perimeter close (flood barrier only; not interior holes).

    - Diagonally opposing solid corners (nw/se or ne/sw)
    - 2x2 blocks with exactly three solid corners (fourth cell sealed)
    - Skips cells in the strict interior of the wall bbox (enclosed holes stay walkable)
    """

    w0, w1, h0, h1 = bbox_bounds
    extra: set[Coord] = set()
    merged = set(solid)
    skip_interior = _strict_bbox_interior_cells(merged)

    for x, y in iter_bbox_cells(w0, w1, h0, h1):
        c = (x, y)
        if c in merged:
            continue
        if c in skip_interior:
            continue
        if _touches_bbox_edge(c, w0, w1, h0, h1):
            continue
        nw = (x - 1, y - 1)
        se = (x + 1, y + 1)
        ne = (x - 1, y + 1)
        sw = (x + 1, y - 1)
        if nw in merged and se in merged:
            extra.add(c)
            merged.add(c)
        elif ne in merged and sw in merged:
            extra.add(c)
            merged.add(c)

    for x in range(w0, w1):
        if x == 0:
            continue
        for y in range(h0, h1):
            block = ((x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1))
            if any(c[0] == 0 for c in block):
                continue
            if block[3][0] > w1 or block[3][1] > h1:
                continue
            in_s = [c for c in block if c in merged]
            if len(in_s) != 3:
                continue
            missing = next(c for c in block if c not in merged)
            if missing in skip_interior:
                continue
            if _touches_bbox_edge(missing, w0, w1, h0, h1):
                continue
            extra.add(missing)
            merged.add(missing)

    return frozenset(extra)


def close_orthogonal_one_cell_slits(
    candidate_void: set[Coord],
    slit_solid: set[Coord],
    bbox_bounds: tuple[int, int, int, int],
) -> frozenset[Coord]:
    """Seal width-1 orthogonal voids opposed by ``slit_solid`` (fixed-point; bbox edge skipped).

    Deprecated: not used by ``pipeline.reconstruct_after_cleanup`` (overcloses external seams).
    Kept for unit-level morphology experiments only.
    """

    w0, w1, h0, h1 = bbox_bounds
    sealed: set[Coord] = set()
    solid = set(slit_solid)

    changed = True
    while changed:
        changed = False
        for c in candidate_void - sealed:
            x, y = c
            if x == 0:
                continue
            if _touches_bbox_edge(c, w0, w1, h0, h1):
                continue
            horizontal = (x - 1, y) in solid and (x + 1, y) in solid
            vertical = (x, y - 1) in solid and (x, y + 1) in solid
            if horizontal or vertical:
                sealed.add(c)
                solid.add(c)
                changed = True

    return frozenset(sealed)
