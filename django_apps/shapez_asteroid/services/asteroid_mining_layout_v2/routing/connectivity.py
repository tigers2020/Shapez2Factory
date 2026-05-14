"""
Read-only connectivity helpers on abstract cell graphs.

Safe for ``validation`` to import: no route construction, no placement mutation.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable


def neighbors4(
    cell: tuple[int, int],
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Unweighted 4-neighbors (cardinal); grid boundary rules applied by caller."""
    x, y = cell
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


def flood_reachable(
    start: tuple[int, int],
    passable: frozenset[tuple[int, int]],
) -> frozenset[tuple[int, int]]:
    """Cells reachable from ``start`` moving only through ``passable`` cells."""
    if start not in passable:
        return frozenset()
    seen: set[tuple[int, int]] = {start}
    q: deque[tuple[int, int]] = deque([start])
    while q:
        c = q.popleft()
        for n in neighbors4(c):
            if n in passable and n not in seen:
                seen.add(n)
                q.append(n)
    return frozenset(seen)


def all_pairs_reachable(
    cells: Iterable[tuple[int, int]],
    passable: frozenset[tuple[int, int]],
) -> bool:
    """True if the subgraph induced by ``cells ∩ passable`` is one connected component."""
    cells_t = frozenset(cells) & passable
    if len(cells_t) <= 1:
        return True
    start = next(iter(cells_t))
    reach = flood_reachable(start, passable)
    return cells_t <= reach
