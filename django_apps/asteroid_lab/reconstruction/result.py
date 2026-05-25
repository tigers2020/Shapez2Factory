"""Reconstruction pipeline result DTO."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


@dataclass(frozen=True, slots=True)
class ReconstructionResult:
    """Output of reconstruction pipeline.

    ``cells`` is the reconstruction **overlay** (sparse replaces), not the complete map.
    Use :func:`build_reconstruction_complete_map` for terrain / capacity / mineable SoT.
    """

    cells: tuple[DecodedCellDTO, ...]  # overlay only
    summary_json: dict[str, Any] = field(default_factory=dict)
    outer_rim_coords: tuple[tuple[int, int], ...] = ()
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW
    confirmed_cells: frozenset[Coord] = field(default_factory=frozenset)
    ambiguous_cells: frozenset[Coord] = field(default_factory=frozenset)
    external_void_cells: frozenset[Coord] = field(default_factory=frozenset)
    confidence_score: float = 1.0
    confidence_by_cell: tuple[tuple[Coord, float], ...] = ()
    quality_flags: frozenset[str] = field(default_factory=frozenset)
    quality_tier: str = "CONFIDENT_RECONSTRUCTION"
