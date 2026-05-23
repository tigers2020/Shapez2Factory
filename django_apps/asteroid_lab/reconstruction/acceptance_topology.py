"""Reconstruction acceptance topology (mineable / external void) without OptimizationInput."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.reconstruction.evidence import (
    evidence_field_kind,
    inferred_field_kind_from_removed_miner_extension,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import ServerCoord, server_coord_to_tuple
from django_apps.asteroid_lab.snapshots.grid_contract import (
    OUTER_VOID_PADDING,
    Coord,
    bbox_from_coords,
    cells_in_bbox,
    expand_bbox,
)
from django_apps.asteroid_lab.snapshots.server_coords import (
    server_xy_for_raw_xy,
    unpack_server_xy_params,
)


def server_coord_for_cell(cell: DecodedCellDTO, params: tuple[int, int] | None) -> ServerCoord:
    sx, sy = cell.server_x, cell.server_y
    if isinstance(sx, int) and isinstance(sy, int):
        return ServerCoord(sx, sy)
    if params is not None:
        md, my, hz = unpack_server_xy_params(params)
        tx, ty = server_xy_for_raw_xy(
            cell.x,
            cell.y,
            min_dense_x=md,
            min_raw_y=my,
            has_explicit_raw_x_zero=hz,
        )
        return ServerCoord(tx, ty)
    msg = "DecodedCellDTO.server_x/server_y missing and ReconstructionResult.server_xy_params unset"
    raise ValueError(msg)


def mineable_field_kind(cell: DecodedCellDTO) -> str | None:
    """Adapter-only field kind for mineable sets (does not mutate ``cell``)."""

    inferred = inferred_field_kind_from_removed_miner_extension(cell)
    if inferred is not None:
        return inferred
    return evidence_field_kind(cell)


@dataclass(frozen=True, slots=True)
class AcceptanceTopology:
    """Server-coordinate sets used by reconstruction confidence / acceptance."""

    mineable_cells: frozenset[Coord]
    external_void_cells: frozenset[Coord]


def _cells_by_server_coord(
    cells: tuple[DecodedCellDTO, ...],
    params: tuple[int, int] | None,
) -> dict[Coord, DecodedCellDTO]:
    by_sv: dict[Coord, DecodedCellDTO] = {}
    for cell in cells:
        sc = server_coord_for_cell(cell, params)
        by_sv[server_coord_to_tuple(sc)] = cell
    return by_sv


def acceptance_topology_from_reconstruction(result: ReconstructionResult) -> AcceptanceTopology:
    """Compute mineable and external void sets for one reconstruction result."""

    cells = result.cells
    params = result.server_xy_params
    by_sv = _cells_by_server_coord(cells, params)

    mineable: set[Coord] = set()
    for sv, cell in by_sv.items():
        if mineable_field_kind(cell) is not None:
            mineable.add(sv)

    mineable_f = frozenset(mineable)
    all_sv = frozenset(by_sv)
    asteroid_bbox = bbox_from_coords(mineable_f if mineable_f else all_sv)
    route_domain_bbox = expand_bbox(asteroid_bbox, OUTER_VOID_PADDING)
    external_void = frozenset(c for c in cells_in_bbox(route_domain_bbox) if c not in all_sv)

    return AcceptanceTopology(
        mineable_cells=mineable_f,
        external_void_cells=external_void,
    )


def mineable_server_coords_from_reconstruction(result: ReconstructionResult) -> frozenset[Coord]:
    return acceptance_topology_from_reconstruction(result).mineable_cells


def external_void_server_coords_from_reconstruction(
    result: ReconstructionResult,
) -> frozenset[Coord]:
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
    violations = 0
    for sv in ambiguous:
        if sv not in topo.mineable_cells:
            violations += 1
    return violations


__all__ = [
    "AcceptanceTopology",
    "acceptance_topology_from_reconstruction",
    "constraint_violation_count",
    "external_void_server_coords_from_reconstruction",
    "mineable_field_kind",
    "mineable_server_coords_from_reconstruction",
    "server_coord_for_cell",
]
