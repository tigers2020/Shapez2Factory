"""Cleanup / deconstruction output (pre-reconstruction).

# wall_coords are topology barriers for flood-fill.
# They include decoded asteroid evidence and synthetic equipment evidence
# from removed extractor/extension cells.
# Removed transport cells are never promoted into wall_coords.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django_apps.asteroid_lab.reconstruction.grid import Coord
from django_apps.asteroid_lab.services.dto import DecodedCellDTO

# Inclusive padded working bbox (w0, w1, h0, h1) for flood-fill; None if no walls.
BBoxBounds = tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class CleanupResult:
    """Output of :func:`deconstruct_snapshot`."""

    cleaned_cells: tuple[DecodedCellDTO, ...]
    removed_building_cells: tuple[DecodedCellDTO, ...]
    ignored_transport_cells: tuple[DecodedCellDTO, ...]
    wall_coords: frozenset[Coord]
    bbox_bounds: BBoxBounds | None
    original_cells: tuple[DecodedCellDTO, ...]
    summary_json: dict[str, Any] = field(default_factory=dict)
