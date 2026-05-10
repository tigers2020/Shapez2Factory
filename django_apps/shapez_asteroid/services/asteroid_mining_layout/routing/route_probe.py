"""Stub→trunk/external route probe (Stabilization-P1).

Uses the same cardinal adjacency rules as ``shapez_grid`` (no tile at ``x==0``).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord

# Cap void expansion for cheap-escape BFS (placement gate only; not STEP4 routing).
_MAX_CHEAP_ESCAPE_VISITS = 20_000


def probe_stub_to_external(
    *,
    stub_cell: Coord,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
) -> bool:
    """True iff a transport-only path exists from ``stub_cell`` to some external cell.

    ``blocked_cells`` typically includes extractor/extension/building bodies; route must not
    traverse them. Only cells in ``transport_cells`` may be used (including ``stub_cell``).
    """

    if stub_cell in blocked_cells or stub_cell not in transport_cells:
        return False
    q: deque[Coord] = deque([stub_cell])
    seen: set[Coord] = {stub_cell}
    while q:
        cur = q.popleft()
        x, y = cur
        for nxt in neighbors4(x, y):
            if is_external(nxt):
                return True
            if nxt in blocked_cells or nxt not in transport_cells or nxt in seen:
                continue
            seen.add(nxt)
            q.append(nxt)
    return False


def probe_stub_cheap_escape_to_external(
    *,
    stub_cell: Coord,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    allowed_void_cells: frozenset[Coord],
) -> bool:
    """True if ``stub_cell`` reaches external via transport and/or bounded void.

    Void steps are allowed only on coordinates in ``allowed_void_cells`` (finite envelope).
    Commits must not add void cells to ``transport_cells``.
    """

    if stub_cell in blocked_cells or stub_cell not in transport_cells:
        return False
    q: deque[Coord] = deque([stub_cell])
    seen: set[Coord] = {stub_cell}
    while q and len(seen) < _MAX_CHEAP_ESCAPE_VISITS:
        cur = q.popleft()
        x, y = cur
        for nxt in neighbors4(x, y):
            if is_external(nxt):
                return True
            if nxt in blocked_cells or nxt in seen:
                continue
            if nxt in transport_cells or nxt in allowed_void_cells:
                seen.add(nxt)
                q.append(nxt)
    return False
