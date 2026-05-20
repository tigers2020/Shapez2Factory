"""Phase A — in-memory reconstruction snapshot for Solver Runtime (no DB I/O)."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO


@dataclass(frozen=True, slots=True)
class LoadedReconstructionSnapshot:
    """Adapter-boundary snapshot preserving reconstruction map metadata (Phase A)."""

    cells: tuple[DecodedCellDTO, ...]
    summary_json: dict[str, Any] = field(default_factory=dict)
    outer_rim_coords: tuple[tuple[int, int], ...] = ()
    server_xy_params: tuple[int, int] | None = None
    confirmed_cells: frozenset[Coord] = field(default_factory=frozenset)
    ambiguous_cells: frozenset[Coord] = field(default_factory=frozenset)
    external_void_cells: frozenset[Coord] = field(default_factory=frozenset)
    confidence_score: float = 1.0
    confidence_by_cell: tuple[tuple[Coord, float], ...] = ()
    quality_flags: frozenset[str] = field(default_factory=frozenset)
    quality_tier: str = "CONFIDENT_RECONSTRUCTION"


def loaded_reconstruction_snapshot_from_result(
    result: ReconstructionResult,
) -> LoadedReconstructionSnapshot:
    """Wrap ``ReconstructionResult`` for Phase A → B adapter boundary."""

    return LoadedReconstructionSnapshot(
        cells=result.cells,
        summary_json=dict(result.summary_json),
        outer_rim_coords=result.outer_rim_coords,
        server_xy_params=result.server_xy_params,
        confirmed_cells=result.confirmed_cells,
        ambiguous_cells=result.ambiguous_cells,
        external_void_cells=result.external_void_cells,
        confidence_score=result.confidence_score,
        confidence_by_cell=result.confidence_by_cell,
        quality_flags=result.quality_flags,
        quality_tier=result.quality_tier,
    )


def loaded_reconstruction_snapshot_from_run(
    cleanup: CleanupResult,
    recon: ReconstructionResult,
) -> LoadedReconstructionSnapshot:
    """Phase A snapshot with Lab-parity display cells (structural cleanup + recon overlay)."""

    from django_apps.asteroid_lab.reconstruction.display_map import (
        merged_display_cells_from_reconstruction,
    )

    base = loaded_reconstruction_snapshot_from_result(recon)
    merged = merged_display_cells_from_reconstruction(cleanup, recon)
    return replace(base, cells=merged)
