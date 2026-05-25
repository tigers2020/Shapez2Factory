"""Terrain rim highlight DTO for Lab replay (UI observability only)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.reconstruction.rim_topology import field_rim_cells
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_EDGE_ORDER = "nesw"
_EDGE_NEIGHBOR: dict[str, tuple[int, int]] = {
    "n": (0, -1),
    "e": (1, 0),
    "s": (0, 1),
    "w": (-1, 0),
}

# Cell (x, y) occupies [x, x+1] × [y, y+1] in corner lattice coords (y grows down-screen).
_VOID_SIDE_SEGMENTS: tuple[tuple[str, tuple[Coord, Coord]], ...] = (
    ("n", ((0, 0), (1, 0))),
    ("e", ((1, 0), (1, 1))),
    ("s", ((1, 1), (0, 1))),
    ("w", ((0, 1), (0, 0))),
)


@dataclass(frozen=True, slots=True)
class VoidEdgeCellDTO:
    x: int
    y: int
    edges: str


@dataclass(frozen=True, slots=True)
class TerrainRimHighlightDTO:
    version: int
    rim_cells: tuple[tuple[int, int], ...]
    void_edge_cells: tuple[VoidEdgeCellDTO, ...]
    outer_outline_loops: tuple[tuple[tuple[int, int], ...], ...]
    coord_frame: CoordFrame


def canonicalize_void_edges(edges: str) -> str:
    """Validate and return canonical ``n``/``e``/``s``/``w`` edge string."""

    if not edges:
        msg = "void edges must not be empty"
        raise ValueError(msg)
    seen: set[str] = set()
    for ch in edges:
        if ch not in _EDGE_NEIGHBOR:
            msg = f"unknown void edge char: {ch!r}"
            raise ValueError(msg)
        seen.add(ch)
    return "".join(ch for ch in _EDGE_ORDER if ch in seen)


def _void_edge_cells(
    rim_cells: frozenset[Coord],
    *,
    external_void_cells: frozenset[Coord],
) -> tuple[VoidEdgeCellDTO, ...]:
    out: list[VoidEdgeCellDTO] = []
    for x, y in sorted(rim_cells):
        edge_chars: list[str] = []
        for ch, (dx, dy) in _EDGE_NEIGHBOR.items():
            if (x + dx, y + dy) in external_void_cells:
                edge_chars.append(ch)
        if not edge_chars:
            continue
        edges = canonicalize_void_edges("".join(edge_chars))
        out.append(VoidEdgeCellDTO(x=x, y=y, edges=edges))
    return tuple(out)


def _void_boundary_segments(
    field_cells: frozenset[Coord],
    *,
    external_void_cells: frozenset[Coord],
) -> list[tuple[Coord, Coord]]:
    segments: list[tuple[Coord, Coord]] = []
    for x, y in field_cells:
        for ch, (dx, dy) in _EDGE_NEIGHBOR.items():
            if (x + dx, y + dy) not in external_void_cells:
                continue
            for side_ch, ((ax, ay), (bx, by)) in _VOID_SIDE_SEGMENTS:
                if side_ch != ch:
                    continue
                segments.append(((x + ax, y + ay), (x + bx, y + by)))
                break
    return segments


def _normalize_edge(a: Coord, b: Coord) -> tuple[Coord, Coord]:
    return (a, b) if a <= b else (b, a)


def _trace_outline_loops(
    segments: list[tuple[Coord, Coord]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
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


def _outer_outline_loops(
    field_cells: frozenset[Coord],
    *,
    external_void_cells: frozenset[Coord],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    segments = _void_boundary_segments(field_cells, external_void_cells=external_void_cells)
    return _trace_outline_loops(segments)


def build_terrain_rim_highlight_from_renderable_cells(
    *,
    field_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord],
    coord_frame: CoordFrame,
) -> TerrainRimHighlightDTO:
    """Replay/UI enrichment only — not solver input."""

    rim = field_rim_cells(field_cells)
    return TerrainRimHighlightDTO(
        version=1,
        rim_cells=tuple(sorted(rim)),
        void_edge_cells=_void_edge_cells(rim, external_void_cells=external_void_cells),
        outer_outline_loops=_outer_outline_loops(
            field_cells,
            external_void_cells=external_void_cells,
        ),
        coord_frame=coord_frame,
    )


def build_terrain_rim_highlight(complete_map: ReconstructionCompleteMap) -> TerrainRimHighlightDTO:
    """Rim + void edges from reconstruction-complete map SoT."""

    return build_terrain_rim_highlight_from_renderable_cells(
        field_cells=complete_map.field_cells,
        external_void_cells=complete_map.external_void_cells,
        coord_frame=complete_map.coord_frame,
    )


def terrain_rim_highlight_to_metrics_dict(dto: TerrainRimHighlightDTO) -> dict[str, object]:
    """JSON-serializable wire for ``metrics.terrain_rim_highlight``."""

    return {
        "version": int(dto.version),
        "coord_frame": dto.coord_frame.value,
        "rim_cells": [[int(x), int(y)] for x, y in dto.rim_cells],
        "void_edge_cells": [
            {"x": int(entry.x), "y": int(entry.y), "edges": entry.edges}
            for entry in dto.void_edge_cells
        ],
        "outer_outline_loops": [
            [[int(x), int(y)] for x, y in loop] for loop in dto.outer_outline_loops
        ],
    }


__all__ = [
    "TerrainRimHighlightDTO",
    "VoidEdgeCellDTO",
    "build_terrain_rim_highlight",
    "build_terrain_rim_highlight_from_renderable_cells",
    "canonicalize_void_edges",
    "terrain_rim_highlight_to_metrics_dict",
]
