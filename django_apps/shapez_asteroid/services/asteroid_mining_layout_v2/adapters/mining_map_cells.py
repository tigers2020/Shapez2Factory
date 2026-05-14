"""``list[dict]`` mining map helpers (blueprint / copy-preview merge).

Replaces legacy ``final_validation.cells_dict_from_mining_map`` and
``routing_cells.mineable_and_asteroid_coords`` for merge-only callers. No v1 imports.
"""

from __future__ import annotations

from typing import Any


def cells_dict_from_mining_map(
    mining_map: list[dict[str, Any]],
) -> dict[tuple[int, int], dict[str, Any]]:
    """Coordinate ``(x, y)`` → cell row shallow copy (same row keys as input)."""

    out: dict[tuple[int, int], dict[str, Any]] = {}
    for row in mining_map:
        if not isinstance(row, dict):
            continue
        x, y = row.get("x"), row.get("y")
        if not isinstance(x, int) or not isinstance(y, int):
            continue
        out[(x, y)] = dict(row)
    return out


def mineable_coords_for_transport_final_merge(
    final_cells: dict[tuple[int, int], dict[str, Any]],
) -> frozenset[tuple[int, int]]:
    """Coords in ``final`` map that may receive interior / field rows from merge logic."""

    out: set[tuple[int, int]] = set()
    for coord, row in final_cells.items():
        if row.get("role") == "inferred":
            out.add(coord)
            continue
        if row.get("layout_kind") == "asteroid_field":
            out.add(coord)
    return frozenset(out)


def mineable_and_asteroid_coords(
    mining_map: list[dict[str, Any]],
) -> tuple[frozenset[tuple[int, int]], frozenset[tuple[int, int]]]:
    """``(mineable, asteroid)`` — ``asteroid`` is every cell key in the map (legacy shape)."""

    final_cells = cells_dict_from_mining_map(mining_map)
    mineable = mineable_coords_for_transport_final_merge(final_cells)
    asteroid = frozenset(final_cells.keys())
    return mineable, asteroid
