"""External void flood fill from padded bbox border (walkable cells only)."""

from __future__ import annotations

from collections import deque

from django_apps.asteroid_lab.reconstruction.grid import Coord
from django_apps.asteroid_lab.snapshots.transport_components import iter_four_neighbors


def external_reachable(
    walkable: set[Coord],
    *,
    w0: int,
    w1: int,
    h0: int,
    h1: int,
) -> set[Coord]:
    """Cells in ``walkable`` reachable from the bbox border via 4-neighbor moves within bbox."""

    q: deque[Coord] = deque()
    seen: set[Coord] = set()

    def try_enqueue(x: int, y: int) -> None:
        if x == 0:
            return
        if x < w0 or x > w1 or y < h0 or y > h1:
            return
        c = (x, y)
        if c not in walkable or c in seen:
            return
        seen.add(c)
        q.append(c)

    for x in range(w0, w1 + 1):
        if x == 0:
            continue
        try_enqueue(x, h0)
        try_enqueue(x, h1)
    for y in range(h0, h1 + 1):
        if w0 != 0:
            try_enqueue(w0, y)
        if w1 != 0:
            try_enqueue(w1, y)

    while q:
        x, y = q.popleft()
        for nx, ny, _nl in iter_four_neighbors(x, y, None):
            try_enqueue(nx, ny)

    return seen
