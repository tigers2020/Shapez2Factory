"""Shim — relocated to ``shapez2_factory.domain.asteroid_lab.asteroid_map_coords`` (PR-CLI-2c)."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.asteroid_map_coords import (
    iter_four_neighbors_map,
    left_of,
    neighbors4_world,
    right_of,
    visual_col,
    world_raw_coord,
)

__all__ = [
    "iter_four_neighbors_map",
    "left_of",
    "neighbors4_world",
    "right_of",
    "visual_col",
    "world_raw_coord",
]
