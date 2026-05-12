"""Existing layout transport component helpers."""

from __future__ import annotations

from collections import deque
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


def role_transport_cells(
    cells: dict[Coord, dict[str, Any]],
    want_role: str,
) -> set[Coord]:
    out: set[Coord] = set()
    for c, row in cells.items():
        if row.get("role") == want_role:
            out.add(c)
    return out


def components_for_role(transport_cells: set[Coord]) -> list[frozenset[Coord]]:
    """4-neighbor connected components within ``transport_cells``."""

    remaining = set(transport_cells)
    comps: list[frozenset[Coord]] = []
    while remaining:
        start = min(remaining, key=lambda p: (p[1], p[0]))
        q: deque[Coord] = deque([start])
        seen: set[Coord] = {start}
        remaining.remove(start)
        while q:
            c = q.popleft()
            x, y = c
            for nxt in neighbors4(x, y):
                if nxt not in remaining or nxt in seen:
                    continue
                seen.add(nxt)
                remaining.remove(nxt)
                q.append(nxt)
        comps.append(frozenset(seen))
    return comps


def coord_key(c: Coord) -> tuple[int, int]:
    return (c[1], c[0])


def bbox_of_cells(cs: frozenset[Coord]) -> tuple[int, int, int, int]:
    xs = [p[0] for p in cs]
    ys = [p[1] for p in cs]
    return min(xs), max(xs), min(ys), max(ys)


def neighbor_transport_cells(
    cells: dict[Coord, dict[str, Any]],
    extractor_coord: Coord,
    want_kind: str,
) -> list[Coord]:
    x, y = extractor_coord
    out: list[Coord] = []
    for nxt in neighbors4(x, y):
        row = cells.get(nxt)
        if row is None:
            continue
        if want_kind == "shape_belt" and row.get("role") == "belt":
            out.append(nxt)
        elif want_kind == "fluid_pipe" and row.get("role") == "pipe":
            out.append(nxt)
    return out


def cell_component_maps(
    comps: list[frozenset[Coord]],
) -> tuple[dict[Coord, int], dict[int, frozenset[Coord]]]:
    cell_to_id: dict[Coord, int] = {}
    by_id: dict[int, frozenset[Coord]] = {}
    for i, comp in enumerate(comps):
        by_id[i] = comp
        for c in comp:
            cell_to_id[c] = i
    return cell_to_id, by_id
