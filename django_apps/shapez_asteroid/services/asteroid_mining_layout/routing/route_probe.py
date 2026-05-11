"""Stub→trunk/external route probe (Stabilization-P1).

Uses the same cardinal adjacency rules as ``shapez_grid`` (no tile at ``x==0``).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord

# Cap void expansion for cheap-escape BFS (placement gate only; not STEP4 routing).
_MAX_CHEAP_ESCAPE_VISITS = 20_000


def _bfs_stub_transport_only(
    *,
    stub_cell: Coord,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
) -> tuple[bool, dict[str, Any]]:
    """Transport-graph BFS from stub; second value is trace detail (success or failure)."""

    if stub_cell in blocked_cells:
        return False, {"transport_probe": {"invalid_stub": "blocked"}}
    if stub_cell not in transport_cells:
        return False, {"transport_probe": {"invalid_stub": "not_in_transport_graph"}}
    q: deque[Coord] = deque([stub_cell])
    seen: set[Coord] = {stub_cell}
    while q:
        cur = q.popleft()
        x, y = cur
        for nxt in neighbors4(x, y):
            if is_external(nxt):
                return True, {"transport_probe": {"reachable_cells_in_component": len(seen)}}
            if nxt in blocked_cells or nxt not in transport_cells or nxt in seen:
                continue
            seen.add(nxt)
            q.append(nxt)
    return False, {
        "transport_probe": {
            "failure": "no_transport_path_to_external",
            "reachable_cells_in_component": len(seen),
        }
    }


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

    ok, _detail = _bfs_stub_transport_only(
        stub_cell=stub_cell,
        transport_cells=transport_cells,
        blocked_cells=blocked_cells,
        is_external=is_external,
    )
    return ok


def probe_stub_to_external_detail(
    *,
    stub_cell: Coord,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
) -> tuple[bool, dict[str, Any]]:
    """Same as ``probe_stub_to_external`` plus a small diagnosis dict for NDJSON tracing."""

    return _bfs_stub_transport_only(
        stub_cell=stub_cell,
        transport_cells=transport_cells,
        blocked_cells=blocked_cells,
        is_external=is_external,
    )


def _bfs_stub_cheap_escape(
    *,
    stub_cell: Coord,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    allowed_void_cells: frozenset[Coord],
) -> tuple[bool, dict[str, Any]]:
    if stub_cell in blocked_cells:
        return False, {"cheap_escape_probe": {"invalid_stub": "blocked"}}
    if stub_cell not in transport_cells:
        return False, {"cheap_escape_probe": {"invalid_stub": "not_in_transport_graph"}}
    q: deque[Coord] = deque([stub_cell])
    seen: set[Coord] = {stub_cell}
    while q and len(seen) < _MAX_CHEAP_ESCAPE_VISITS:
        cur = q.popleft()
        x, y = cur
        for nxt in neighbors4(x, y):
            if is_external(nxt):
                return True, {"cheap_escape_probe": {"visited_cells": len(seen)}}
            if nxt in blocked_cells or nxt in seen:
                continue
            if nxt in transport_cells or nxt in allowed_void_cells:
                seen.add(nxt)
                q.append(nxt)
    visit_cap_hit = len(seen) >= _MAX_CHEAP_ESCAPE_VISITS
    return False, {
        "cheap_escape_probe": {
            "failure": "no_path_or_visit_cap",
            "visited_cells": len(seen),
            "visit_cap_hit": visit_cap_hit,
            "visit_cap": _MAX_CHEAP_ESCAPE_VISITS,
        }
    }


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

    ok, _detail = _bfs_stub_cheap_escape(
        stub_cell=stub_cell,
        transport_cells=transport_cells,
        blocked_cells=blocked_cells,
        is_external=is_external,
        allowed_void_cells=allowed_void_cells,
    )
    return ok


def probe_stub_cheap_escape_to_external_detail(
    *,
    stub_cell: Coord,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    allowed_void_cells: frozenset[Coord],
) -> tuple[bool, dict[str, Any]]:
    """Cheap-escape BFS with diagnosis dict for NDJSON tracing."""

    return _bfs_stub_cheap_escape(
        stub_cell=stub_cell,
        transport_cells=transport_cells,
        blocked_cells=blocked_cells,
        is_external=is_external,
        allowed_void_cells=allowed_void_cells,
    )
