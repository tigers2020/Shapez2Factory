"""Infer asteroid patch interior cells from extraction perimeter (STEP 1 helper).

Ported from legacy ``asteroid_patch_interior`` (morphological closing + outside flood).
No Django; no v1 ``asteroid_mining_layout`` imports.
"""

from __future__ import annotations

from collections import deque

_NEI4: tuple[tuple[int, int], ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))

_NEI8: tuple[tuple[int, int], ...] = tuple(
    (dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)
)


def _is_narrow_slit_gap(cell: tuple[int, int], occupied: set[tuple[int, int]]) -> bool:
    x, y = cell
    if (x, y) in occupied:
        return False
    if (x - 1, y) in occupied and (x + 1, y) in occupied:
        if (x, y - 1) not in occupied and (x, y + 1) not in occupied:
            return True
    if (x, y - 1) in occupied and (x, y + 1) in occupied:
        if (x - 1, y) not in occupied and (x + 1, y) not in occupied:
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
    return any((x + dx, y + dy) in outside for dx, dy in _NEI8)


def dilate_chebyshev(cells: set[tuple[int, int]], steps: int) -> set[tuple[int, int]]:
    s = set(cells)
    for _ in range(max(0, steps)):
        nxt = set(s)
        for x, y in s:
            for dx, dy in _NEI8:
                nxt.add((x + dx, y + dy))
        s = nxt
    return s


def erode_chebyshev(cells: set[tuple[int, int]], steps: int) -> set[tuple[int, int]]:
    s = set(cells)
    for _ in range(max(0, steps)):
        nxt: set[tuple[int, int]] = set()
        for x, y in s:
            if all((x + dx, y + dy) in s for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                nxt.add((x, y))
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
        for y in range(ay0, ay1 + 1):
            on_edge = x == ax0 or x == ax1 or y == ay0 or y == ay1
            if on_edge and (x, y) not in blocked:
                q.append((x, y))
                outside.add((x, y))

    while q:
        x, y = q.popleft()
        for dx, dy in _NEI4:
            nx, ny = x + dx, y + dy
            if nx < ax0 or nx > ax1 or ny < ay0 or ny > ay1:
                continue
            if (nx, ny) in blocked or (nx, ny) in outside:
                continue
            outside.add((nx, ny))
            q.append((nx, ny))

    interior: list[tuple[int, int]] = []
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            if (x, y) in occupied or (x, y) in outside:
                continue
            if any((x + dx, y + dy) in outside for dx, dy in _NEI4):
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
