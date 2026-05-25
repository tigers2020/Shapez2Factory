"""Test helpers for ``ReconstructionCompleteMap`` without full cleanup merge."""

from __future__ import annotations

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_decoded_cells,
)
from django_apps.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
    _count_by_resource,
    _field_cells_from_decoded_cells,
    build_reconstruction_complete_map,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame


def minimal_complete_map_from_cells(
    *cells: DecodedCellDTO,
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW,
) -> ReconstructionCompleteMap:
    """Complete map whose ``cells`` tuple is exactly ``cells`` (unit tests only)."""

    cell_tuple = tuple(cells)
    field_cells = _field_cells_from_decoded_cells(cell_tuple, coord_frame=coord_frame)
    by_resource = _count_by_resource(cell_tuple)
    topo = acceptance_topology_from_decoded_cells(
        cell_tuple,
        field_cells=field_cells,
        coord_frame=coord_frame,
    )
    return ReconstructionCompleteMap(
        cells=cell_tuple,
        field_cells=field_cells,
        shape_field_cell_count=by_resource["shape"],
        fluid_field_cell_count=by_resource["fluid"],
        external_void_cells=topo.external_void_cells,
        coord_frame=coord_frame,
    )


def minimal_cleanup_and_recon_from_cells(
    *cells: DecodedCellDTO,
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW,
) -> tuple[CleanupResult, ReconstructionResult]:
    """Greenfield-style cleanup where overlay cells are the full field grid."""

    cell_tuple = tuple(cells)
    cleanup = CleanupResult(
        cleaned_cells=cell_tuple,
        removed_building_cells=(),
        ignored_transport_cells=(),
        wall_coords=frozenset(),
        bbox_bounds=None,
        original_cells=cell_tuple,
    )
    recon = ReconstructionResult(
        cells=cell_tuple,
        confirmed_cells=frozenset(),
        ambiguous_cells=frozenset(),
        external_void_cells=frozenset(),
        confidence_score=1.0,
        quality_tier="CONFIDENT_RECONSTRUCTION",
        coord_frame=coord_frame,
    )
    return cleanup, recon


def complete_map_from_overlay_cells(
    *cells: DecodedCellDTO,
) -> ReconstructionCompleteMap:
    cleanup, recon = minimal_cleanup_and_recon_from_cells(*cells)
    return build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
