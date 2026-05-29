"""Corner-lattice hull outlines for occupied unit cells (geometry only).

Used by terrain rim void-facing boundaries and pattern-bundle equipment footprints.
Rim-specific void segment rules stay in ``rim_highlight.py``.
"""

from __future__ import annotations

from collections import defaultdict

from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_EDGE_NEIGHBOR: dict[str, tuple[int, int]] = {
    "n": (0, -1),
    "e": (1, 0),
    "s": (0, 1),
    "w": (-1, 0),
}

# Cell (x, y) occupies [x, x+1] × [y, y+1] in corner lattice coords (y grows down-screen).
_CELL_SIDE_SEGMENTS: tuple[tuple[str, tuple[Coord, Coord]], ...] = (
    ("n", ((0, 0), (1, 0))),
    ("e", ((1, 0), (1, 1))),
    ("s", ((1, 1), (0, 1))),
    ("w", ((0, 1), (0, 0))),
)


def _normalize_edge(a: Coord, b: Coord) -> tuple[Coord, Coord]:
    return (a, b) if a <= b else (b, a)


def trace_outline_loops_from_segments(
    segments: list[tuple[Coord, Coord]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Chain undirected corner segments into closed loop(s)."""

    if not segments:
        return ()

    adj: dict[Coord, list[Coord]] = defaultdict(list)
    edges: list[tuple[Coord, Coord]] = []
    for a, b in segments:
        adj[a].append(b)
        adj[b].append(a)
        edges.append(_normalize_edge(a, b))

    used: set[tuple[Coord, Coord]] = set()
    loops: list[tuple[tuple[int, int], ...]] = []

    for edge in edges:
        if edge in used:
            continue
        start_a, start_b = edge
        path: list[tuple[int, int]] = [start_a, start_b]
        used.add(edge)
        cur = start_b
        while cur != start_a:
            next_candidates = [nxt for nxt in adj[cur] if _normalize_edge(cur, nxt) not in used]
            if not next_candidates:
                path = []
                break
            nxt = next_candidates[0]
            used.add(_normalize_edge(cur, nxt))
            path.append(nxt)
            cur = nxt
        if len(path) >= 3 and cur == start_a:
            closed = tuple(path) + (start_a,)
            if len(closed) >= 4:
                loops.append(closed)

    if not loops:
        return ()

    loops_sorted = sorted(loops, key=len, reverse=True)
    return tuple(loops_sorted)


def exterior_segments_for_occupied_cells(
    occupied: frozenset[Coord],
) -> list[tuple[Coord, Coord]]:
    """Side segments on the hull where a 4-neighbor is outside ``occupied``."""

    segments: list[tuple[Coord, Coord]] = []
    for x, y in occupied:
        for ch, (dx, dy) in _EDGE_NEIGHBOR.items():
            if (x + dx, y + dy) in occupied:
                continue
            for side_ch, ((ax, ay), (bx, by)) in _CELL_SIDE_SEGMENTS:
                if side_ch != ch:
                    continue
                segments.append(((x + ax, y + ay), (x + bx, y + by)))
                break
    return segments


def build_cell_hull_outline_loops(
    occupied: frozenset[Coord],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Closed outline loop(s) around ``occupied`` unit cells."""

    if not occupied:
        return ()
    segments = exterior_segments_for_occupied_cells(occupied)
    return trace_outline_loops_from_segments(segments)


__all__ = [
    "build_cell_hull_outline_loops",
    "exterior_segments_for_occupied_cells",
    "trace_outline_loops_from_segments",
]
