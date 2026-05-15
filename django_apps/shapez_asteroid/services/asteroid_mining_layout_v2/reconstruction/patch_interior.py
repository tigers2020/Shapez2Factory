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


def _occupied_axis_extents(occupied: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    xs = [x for x, _ in occupied]
    ys = [y for _, y in occupied]
    return min(xs), max(xs), min(ys), max(ys)


def _padded_scan_bounds(
    x_min: int, x_max: int, y_min: int, y_max: int
) -> tuple[int, int, int, int]:
    return x_min - 1, x_max + 1, y_min - 1, y_max + 1


def _on_scan_frame_edge(x: int, y: int, ax0: int, ax1: int, ay0: int, ay1: int) -> bool:
    return x == ax0 or x == ax1 or y == ay0 or y == ay1


def _seed_outside_from_frame_edges(
    blocked: set[tuple[int, int]],
    ax0: int,
    ax1: int,
    ay0: int,
    ay1: int,
) -> tuple[set[tuple[int, int]], deque[tuple[int, int]]]:
    outside: set[tuple[int, int]] = set()
    q: deque[tuple[int, int]] = deque()
    for x in range(ax0, ax1 + 1):
        if not is_physical_x(x):
            continue
        for y in range(ay0, ay1 + 1):
            if not _on_scan_frame_edge(x, y, ax0, ax1, ay0, ay1):
                continue
            if (x, y) in blocked:
                continue
            cell = (x, y)
            q.append(cell)
            outside.add(cell)
    return outside, q


def _flood_outside_reachable(
    blocked: set[tuple[int, int]],
    ax0: int,
    ax1: int,
    ay0: int,
    ay1: int,
    outside: set[tuple[int, int]],
    q: deque[tuple[int, int]],
) -> None:
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


def _build_outside_set(
    blocked: set[tuple[int, int]],
    ax0: int,
    ax1: int,
    ay0: int,
    ay1: int,
) -> set[tuple[int, int]]:
    outside, q = _seed_outside_from_frame_edges(blocked, ax0, ax1, ay0, ay1)
    _flood_outside_reachable(blocked, ax0, ax1, ay0, ay1, outside, q)
    return outside


def _interior_cell_excluded(
    cell: tuple[int, int],
    occupied: set[tuple[int, int]],
    outside: set[tuple[int, int]],
) -> bool:
    x, y = cell
    if cell in occupied or cell in outside:
        return True
    if any(n in outside for n in cardinal_neighbors4((x, y))):
        return True
    if _slit_touching_outside(cell, occupied, outside):
        return True
    return False


def _interior_cells_sorted_yx(
    x_min: int,
    x_max: int,
    y_min: int,
    y_max: int,
    occupied: set[tuple[int, int]],
    outside: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    interior: list[tuple[int, int]] = []
    for x in iter_physical_x_in_range(x_min, x_max):
        for y in range(y_min, y_max + 1):
            if _interior_cell_excluded((x, y), occupied, outside):
                continue
            interior.append((x, y))
    interior.sort(key=lambda c: (c[1], c[0]))
    return interior


def compute_patch_interior_cells(
    occupied: set[tuple[int, int]],
    *,
    perimeter_bridge_steps: int = 1,
) -> list[tuple[int, int]]:
    if len(occupied) < 4:
        return []

    x_min, x_max, y_min, y_max = _occupied_axis_extents(occupied)
    blocked = closing_chebyshev(occupied, perimeter_bridge_steps)
    ax0, ax1, ay0, ay1 = _padded_scan_bounds(x_min, x_max, y_min, y_max)
    outside = _build_outside_set(blocked, ax0, ax1, ay0, ay1)
    return _interior_cells_sorted_yx(x_min, x_max, y_min, y_max, occupied, outside)


__all__ = [
    "closing_chebyshev",
    "compute_patch_interior_cells",
    "dilate_chebyshev",
    "erode_chebyshev",
]
