"""Shim: relocated to ``shapez2_factory.domain.asteroid_lab.grid_contract`` (PR-CLI-2a).

This module re-exports the pure core DTOs so existing ``django_apps`` imports keep working.
Import the core module directly in new code.
"""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.grid_contract import (
    OUTER_VOID_PADDING,
    BBox,
    Coord,
    bbox_from_coords,
    cells_in_bbox,
    expand_bbox,
    neighbors4,
)

__all__ = [
    "BBox",
    "Coord",
    "OUTER_VOID_PADDING",
    "bbox_from_coords",
    "cells_in_bbox",
    "expand_bbox",
    "neighbors4",
]
