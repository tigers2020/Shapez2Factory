"""Infer asteroid patch interior cells from extraction perimeter (STEP 1 helper).

Ported from legacy ``asteroid_patch_interior`` (morphological closing + outside flood).
No Django; no v1 ``asteroid_mining_layout`` imports.

Uses ``domain.grid`` on top of ``domain.coord`` (no ``x == 0`` column): neighbors and
bbox scans never treat ``(0, y)`` as grid cells.
"""

from __future__ import annotations

from collections import deque

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    is_physical_x,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.grid import (
    cardinal_neighbors4,
    chebyshev_neighbors8,
    iter_physical_x_in_range,
    step_blueprint_cell,
)


def _is_narrow_slit_gap(cell: tuple[int, int], occupied: set[tuple[int, int]]) -> bool:
    x, y = cell
    if (x, y) in occupied or not is_physical_x(x):
        return False
    west = step_blueprint_cell((x, y), (-1, 0))
    east = step_blueprint_cell((x, y), (1, 0))
    if west in occupied and east in occupied:
        if (x, y - 1) not in occupied and (x, y + 1) not in occupied:
            return True
    if (x, y - 1) in occupied and (x, y + 1) in occupied:
        if west not in occupied and east not in occupied:
            return True
    return False


def _slit_touching_outside(
    cell: tuple[int, int],
    occupied: set[tuple[int, int]],
    outside: set[tuple[int, int]],
) -> bool:
    if not _is_narrow_slit_gap(cell, occupied):
        return False
    x, y = cell
    return any(n in outside for n in chebyshev_neighbors8((x, y)))


def dilate_chebyshev(cells: set[tuple[int, int]], steps: int) -> set[tuple[int, int]]:
    s = set(cells)
    for _ in range(max(0, steps)):
        nxt = set(s)
        for c in s:
            nxt |= chebyshev_neighbors8(c)
        s = nxt
    return s


def erode_chebyshev(cells: set[tuple[int, int]], steps: int) -> set[tuple[int, int]]:
    s = set(cells)
    for _ in range(max(0, steps)):
        nxt: set[tuple[int, int]] = set()
        for c in s:
            ball = frozenset({c}) | chebyshev_neighbors8(c)
            if ball <= s:
                nxt.add(c)
        s = nxt
    return s


def closing_chebyshev(cells: set[tuple[int, int]], steps: int) -> set[tuple[int, int]]:
    return erode_chebyshev(dilate_chebyshev(cells, steps), steps)


def compute_patch_interior_cells(
    occupied: set[tuple[int, int]],
    *,
    perimeter_bridge_steps: int = 1,
) -> list[tuple[int, int]]:
    if len(occupied) < 4:
        return []

    xs = [x for x, _ in occupied]
    ys = [y for _, y in occupied]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    blocked = closing_chebyshev(occupied, perimeter_bridge_steps)

    ax0, ax1 = x_min - 1, x_max + 1
    ay0, ay1 = y_min - 1, y_max + 1

    outside: set[tuple[int, int]] = set()
    q: deque[tuple[int, int]] = deque()

    for x in range(ax0, ax1 + 1):
        if not is_physical_x(x):
            continue
        for y in range(ay0, ay1 + 1):
            on_edge = x == ax0 or x == ax1 or y == ay0 or y == ay1
            if on_edge and (x, y) not in blocked:
                q.append((x, y))
                outside.add((x, y))

    while q:
        cur = q.popleft()
        for nxt in cardinal_neighbors4(cur):
            nx, ny = nxt
            if nx < ax0 or nx > ax1 or ny < ay0 or ny > ay1:
                continue
            if nxt in blocked or nxt in outside:
                continue
            outside.add(nxt)
            q.append(nxt)

    interior: list[tuple[int, int]] = []
    for x in iter_physical_x_in_range(x_min, x_max):
        for y in range(y_min, y_max + 1):
            if (x, y) in occupied or (x, y) in outside:
                continue
            if any(n in outside for n in cardinal_neighbors4((x, y))):
                continue
            if _slit_touching_outside((x, y), occupied, outside):
                continue
            interior.append((x, y))

    interior.sort(key=lambda c: (c[1], c[0]))
    return interior


__all__ = [
    "closing_chebyshev",
    "compute_patch_interior_cells",
    "dilate_chebyshev",
    "erode_chebyshev",
]
