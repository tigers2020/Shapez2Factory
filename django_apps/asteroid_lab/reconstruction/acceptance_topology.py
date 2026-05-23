"""Reconstruction acceptance topology (mineable / external void) without OptimizationInput."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from django_apps.asteroid_lab.reconstruction.evidence import (
    evidence_field_kind,
    inferred_field_kind_from_removed_miner_extension,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import (
    OUTER_VOID_PADDING,
    Coord,
    bbox_from_coords,
    cells_in_bbox,
    expand_bbox,
)


def infer_topology_coord_frame(cells: Sequence[DecodedCellDTO]) -> CoordFrame:
    """Decoded/reconstructed cells use island-local topology."""

    del cells
    return CoordFrame.ISLAND_RAW


def topology_coord_for_cell(
    cell: DecodedCellDTO,
    params: object | None = None,
    *,
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW,
) -> Coord:
    """Mineable / void topology key for one island-local cell."""

    del params
    if coord_frame == CoordFrame.WORLD_RAW:
        msg = "WORLD_RAW acceptance topology not implemented - proof gate required"
        raise ValueError(msg)
    return (cell.x, cell.y)


def mineable_field_kind(cell: DecodedCellDTO) -> str | None:
    """Adapter-only field kind for mineable sets (does not mutate ``cell``)."""

    inferred = inferred_field_kind_from_removed_miner_extension(cell)
    if inferred is not None:
        return inferred
    return evidence_field_kind(cell)


@dataclass(frozen=True, slots=True)
class AcceptanceTopology:
    """Island-coordinate sets used by reconstruction confidence / acceptance."""

    mineable_cells: frozenset[Coord]
    external_void_cells: frozenset[Coord]


def _cells_by_topology_coord(
    cells: tuple[DecodedCellDTO, ...],
    *,
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW,
) -> dict[Coord, DecodedCellDTO]:
    by_coord: dict[Coord, DecodedCellDTO] = {}
    for cell in cells:
        by_coord[topology_coord_for_cell(cell, coord_frame=coord_frame)] = cell
    return by_coord


def acceptance_topology_from_reconstruction(
    result: ReconstructionResult,
    *,
    coord_frame: CoordFrame | None = None,
) -> AcceptanceTopology:
    """Compute mineable and external void sets for one reconstruction result."""

    frame = coord_frame if coord_frame is not None else result.coord_frame
    if frame == CoordFrame.WORLD_RAW:
        msg = "WORLD_RAW acceptance topology not implemented - proof gate required"
        raise ValueError(msg)

    by_coord = _cells_by_topology_coord(result.cells, coord_frame=frame)
    mineable = {coord for coord, cell in by_coord.items() if mineable_field_kind(cell) is not None}

    mineable_f = frozenset(mineable)
    all_coords = frozenset(by_coord)
    asteroid_bbox = bbox_from_coords(mineable_f if mineable_f else all_coords)
    route_domain_bbox = expand_bbox(asteroid_bbox, OUTER_VOID_PADDING)
    external_void = frozenset(c for c in cells_in_bbox(route_domain_bbox) if c not in all_coords)

    return AcceptanceTopology(
        mineable_cells=mineable_f,
        external_void_cells=external_void,
    )


def mineable_coords_from_reconstruction(result: ReconstructionResult) -> frozenset[Coord]:
    return acceptance_topology_from_reconstruction(result).mineable_cells


def external_void_coords_from_reconstruction(result: ReconstructionResult) -> frozenset[Coord]:
    return acceptance_topology_from_reconstruction(result).external_void_cells


def constraint_violation_count(
    result: ReconstructionResult,
    *,
    ambiguous: frozenset[Coord],
) -> int:
    """Count ambiguous cells that fall outside the mineable set."""

    try:
        topo = acceptance_topology_from_reconstruction(result)
    except ValueError:
        return 1
    return sum(1 for coord in ambiguous if coord not in topo.mineable_cells)


__all__ = [
    "AcceptanceTopology",
    "acceptance_topology_from_reconstruction",
    "constraint_violation_count",
    "external_void_coords_from_reconstruction",
    "infer_topology_coord_frame",
    "mineable_coords_from_reconstruction",
    "mineable_field_kind",
    "topology_coord_for_cell",
]
