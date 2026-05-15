"""Infer asteroid **patch interior** cells from extraction perimeter points (grid).

Interior is **gameplay-oriented enclosure**, not strict topological openness: a small
perimeter leak can still be treated as closed (morphological closing on occupied, then
outside flood on the complement).
"""

from __future__ import annotations

from collections import deque

# 8-neighbor (Chebyshev): dilation / erosion disks for closing.
_NEI4: tuple[tuple[int, int], ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))

_NEI8: tuple[tuple[int, int], ...] = tuple(
    (dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)
)


def _is_narrow_slit_gap(cell: tuple[int, int], occupied: set[tuple[int, int]]) -> bool:
    """Axis-aligned 1-cell choke: O-empty-O on one axis and both perpendiculars non-O."""

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
    """Drop slit-shaped cells only near the flood exterior (avoids interior 1-wide runs)."""

    if not _is_narrow_slit_gap(cell, occupied):
        return False
    x, y = cell
    return any((x + dx, y + dy) in outside for dx, dy in _NEI8)


def dilate_chebyshev(cells: set[tuple[int, int]], steps: int) -> set[tuple[int, int]]:
    """Grow ``cells`` by ``steps`` Chebyshev layers (8-neighborhood each step)."""

    s = set(cells)
    for _ in range(max(0, steps)):
        nxt = set(s)
        for x, y in s:
            for dx, dy in _NEI8:
                nxt.add((x + dx, y + dy))
        s = nxt
    return s


def erode_chebyshev(cells: set[tuple[int, int]], steps: int) -> set[tuple[int, int]]:
    """Shrink ``cells`` by ``steps`` Chebyshev layers (3×3 structuring element each step)."""

    s = set(cells)
    for _ in range(max(0, steps)):
        nxt: set[tuple[int, int]] = set()
        for x, y in s:
            if all((x + dx, y + dy) in s for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                nxt.add((x, y))
        s = nxt
    return s


def closing_chebyshev(cells: set[tuple[int, int]], steps: int) -> set[tuple[int, int]]:
    """Morphological closing (dilate then erode) with the same Chebyshev radius."""

    return erode_chebyshev(dilate_chebyshev(cells, steps), steps)


def _tight_bbox(occupied: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    xs = [x for x, _ in occupied]
    ys = [y for _, y in occupied]
    return min(xs), max(xs), min(ys), max(ys)


def _on_expanded_frame(x: int, y: int, ax0: int, ax1: int, ay0: int, ay1: int) -> bool:
    return x == ax0 or x == ax1 or y == ay0 or y == ay1


def _enqueue_4_outside_neighbors(
    x: int,
    y: int,
    *,
    blocked: set[tuple[int, int]],
    outside: set[tuple[int, int]],
    q: deque[tuple[int, int]],
    ax0: int,
    ax1: int,
    ay0: int,
    ay1: int,
) -> None:
    for dx, dy in _NEI4:
        nx, ny = x + dx, y + dy
        if nx < ax0 or nx > ax1 or ny < ay0 or ny > ay1:
            continue
        if (nx, ny) in blocked or (nx, ny) in outside:
            continue
        outside.add((nx, ny))
        q.append((nx, ny))


def _flood_outside_4(
    blocked: set[tuple[int, int]],
    ax0: int,
    ax1: int,
    ay0: int,
    ay1: int,
) -> set[tuple[int, int]]:
    outside: set[tuple[int, int]] = set()
    q: deque[tuple[int, int]] = deque()
    for x in range(ax0, ax1 + 1):
        for y in range(ay0, ay1 + 1):
            if not _on_expanded_frame(x, y, ax0, ax1, ay0, ay1):
                continue
            if (x, y) in blocked:
                continue
            q.append((x, y))
            outside.add((x, y))
    while q:
        cx, cy = q.popleft()
        _enqueue_4_outside_neighbors(
            cx,
            cy,
            blocked=blocked,
            outside=outside,
            q=q,
            ax0=ax0,
            ax1=ax1,
            ay0=ay0,
            ay1=ay1,
        )
    return outside


def _cell_is_enclosed_interior(
    x: int,
    y: int,
    *,
    occupied: set[tuple[int, int]],
    outside: set[tuple[int, int]],
) -> bool:
    if (x, y) in occupied or (x, y) in outside:
        return False
    if any((x + dx, y + dy) in outside for dx, dy in _NEI4):
        return False
    if _slit_touching_outside((x, y), occupied, outside):
        return False
    return True


def compute_patch_interior_cells(
    occupied: set[tuple[int, int]],
    *,
    perimeter_bridge_steps: int = 1,
) -> list[tuple[int, int]]:
    """Return empty grid cells treated as enclosed mineable patch interior.

    ``occupied`` is passed through **Chebyshev closing** (radius ``perimeter_bridge_steps``)
    to obtain the barrier for outside flood fill: narrow gaps in the perimeter are bridged
    without fattening the mask as much as dilation alone.

    Outside flood uses **4-connectivity**; structuring uses **8-connectivity** (gameplay
    closure for diagonal slits and corners).

    Candidates not reachable as outside and not in ``occupied`` are peeled once if they
    share a 4-edge with ``outside``. Remaining axis-aligned **slit** cells are removed
    only when they **8-touch** ``outside`` (perimeter chokes), not long interior 1-wide
    corridors.

    Returned cells lie in the tight bbox of ``occupied``, are not flood-outside, and are
    not in ``occupied``.
    """

    if len(occupied) < 4:
        return []

    x_min, x_max, y_min, y_max = _tight_bbox(occupied)
    blocked = closing_chebyshev(occupied, perimeter_bridge_steps)
    ax0, ax1 = x_min - 1, x_max + 1
    ay0, ay1 = y_min - 1, y_max + 1
    outside = _flood_outside_4(blocked, ax0, ax1, ay0, ay1)

    interior: list[tuple[int, int]] = []
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            if _cell_is_enclosed_interior(x, y, occupied=occupied, outside=outside):
                interior.append((x, y))

    interior.sort(key=lambda c: (c[1], c[0]))
    return interior
