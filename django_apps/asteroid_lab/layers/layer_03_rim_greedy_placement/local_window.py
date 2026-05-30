"""Local DPS search window for rim greedy route probe."""

from __future__ import annotations

from django_apps.asteroid_lab.snapshots.grid_contract import (
    BBox,
    Coord,
    bbox_from_coords,
    expand_bbox,
)


def compute_greedy_search_bbox(
    *,
    equipment_cells: frozenset[Coord],
    stub_cells: frozenset[Coord],
    goal_coords: frozenset[Coord],
    margin: int,
) -> BBox:
    """Inclusive bbox over footprint, stubs, goals, expanded by policy margin."""
    seed_coords = equipment_cells | stub_cells | goal_coords
    base = bbox_from_coords(seed_coords)
    return expand_bbox(base, margin)


__all__ = ["compute_greedy_search_bbox"]
