"""Reconstruction-complete map DTO and sole terrain SoT factory."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_decoded_cells,
)
from django_apps.asteroid_lab.reconstruction.display_map import (
    merged_display_cells_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.evidence import ASTEROID_FIELD_KINDS
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_SHAPE_FIELD = "asteroid_shape_field"
_FLUID_FIELD = "asteroid_fluid_field"


def _field_cells_from_decoded_cells(
    cells: Sequence[DecodedCellDTO],
    *,
    coord_frame: CoordFrame,
) -> frozenset[Coord]:
    if coord_frame == CoordFrame.WORLD_RAW:
        msg = "WORLD_RAW complete map field cells not implemented"
        raise ValueError(msg)
    out: set[Coord] = set()
    for cell in cells:
        if cell.cell_kind not in ASTEROID_FIELD_KINDS:
            continue
        out.add((cell.x, cell.y))
    return frozenset(out)


def _count_by_resource(cells: Sequence[DecodedCellDTO]) -> dict[str, int]:
    counts = {"shape": 0, "fluid": 0}
    for cell in cells:
        if cell.cell_kind == _SHAPE_FIELD:
            counts["shape"] += 1
        elif cell.cell_kind == _FLUID_FIELD:
            counts["fluid"] += 1
    return counts


def overlay_field_cell_count(recon: ReconstructionResult) -> int:
    """Overlay-only count for contract tests (not terrain SoT)."""

    return len(
        _field_cells_from_decoded_cells(recon.cells, coord_frame=recon.coord_frame)
    )


@dataclass(frozen=True, slots=True)
class ReconstructionCompleteMap:
    """Merged cleanup structural map + reconstruction overlay."""

    cells: tuple[DecodedCellDTO, ...]
    field_cells: frozenset[Coord]
    shape_field_cell_count: int
    fluid_field_cell_count: int
    external_void_cells: frozenset[Coord]
    coord_frame: CoordFrame


def build_reconstruction_complete_map(
    *,
    cleanup: CleanupResult,
    recon: ReconstructionResult,
) -> ReconstructionCompleteMap:
    """Sole entry point for reconstruction-complete terrain SoT."""

    cells = merged_display_cells_from_reconstruction(cleanup, recon)
    frame = recon.coord_frame
    field_cells = _field_cells_from_decoded_cells(cells, coord_frame=frame)
    by_resource = _count_by_resource(cells)
    topo = acceptance_topology_from_decoded_cells(
        cells,
        field_cells=field_cells,
        coord_frame=frame,
    )
    return ReconstructionCompleteMap(
        cells=cells,
        field_cells=field_cells,
        shape_field_cell_count=by_resource["shape"],
        fluid_field_cell_count=by_resource["fluid"],
        external_void_cells=topo.external_void_cells,
        coord_frame=frame,
    )


__all__ = [
    "ReconstructionCompleteMap",
    "build_reconstruction_complete_map",
    "overlay_field_cell_count",
]
