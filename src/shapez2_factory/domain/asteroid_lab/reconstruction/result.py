"""Reconstruction pipeline result DTO."""

from __future__ import annotations

from dataclasses import dataclass, field

from shapez2_factory.domain.asteroid_lab.coord_frames import CoordFrame
from shapez2_factory.domain.asteroid_lab.decoded_cell import DecodedCellDTO
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord


@dataclass(frozen=True, slots=True)
class ReconstructionResult:
    """Output of reconstruction pipeline.

    ``cells`` is the reconstruction **overlay** (sparse replaces), not the complete map.
    Use :func:`build_reconstruction_complete_map` for terrain / capacity / mineable SoT.
    """

    cells: tuple[DecodedCellDTO, ...]  # overlay only
    summary_json: dict[str, object] = field(default_factory=dict)
    outer_rim_coords: tuple[tuple[int, int], ...] = ()
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW
    confirmed_cells: frozenset[Coord] = field(default_factory=frozenset)
    ambiguous_cells: frozenset[Coord] = field(default_factory=frozenset)
    external_void_cells: frozenset[Coord] = field(default_factory=frozenset)
    confidence_score: float = 1.0
    confidence_by_cell: tuple[tuple[Coord, float], ...] = ()
    quality_flags: frozenset[str] = field(default_factory=frozenset)
    quality_tier: str = "CONFIDENT_RECONSTRUCTION"
