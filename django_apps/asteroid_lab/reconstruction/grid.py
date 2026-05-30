"""Shim — relocated to ``shapez2_factory.domain.asteroid_lab.reconstruction.grid`` (PR-CLI-2c)."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.reconstruction.grid import (
    Coord,
    iter_bbox_cells,
    padded_bbox_bounds,
    reconstruction_cardinal_neighbors,
)

__all__ = [
    "Coord",
    "iter_bbox_cells",
    "padded_bbox_bounds",
    "reconstruction_cardinal_neighbors",
]
