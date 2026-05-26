"""Post-hoc route/trunk connectivity metrics for recovery evidence (read-only)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.snapshots.grid_contract import neighbors4


def count_exterior_connected_route_cells(
    route_cells: frozenset[Coord],
    trunk_mask_cells: frozenset[Coord],
) -> int:
    """Count route cells in any 4-neighbor component that touches trunk_mask."""

    if not route_cells or not trunk_mask_cells:
        return 0
    seeds = [coord for coord in route_cells if coord in trunk_mask_cells]
    if not seeds:
        seeds = [
            coord
            for coord in route_cells
            if any(neighbor in trunk_mask_cells for neighbor in neighbors4(coord))
        ]
    if not seeds:
        return 0
    connected: set[Coord] = set()
    for start in seeds:
        if start in connected:
            continue
        stack = [start]
        connected.add(start)
        while stack:
            cur = stack.pop()
            for nb in neighbors4(cur):
                if nb in route_cells and nb not in connected:
                    connected.add(nb)
                    stack.append(nb)
    return len(connected)


__all__ = ["count_exterior_connected_route_cells"]
