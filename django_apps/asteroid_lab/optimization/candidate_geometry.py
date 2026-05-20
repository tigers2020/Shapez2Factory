"""Phase F — read-only geometry validation for projected genes (PR2)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import CandidateRejectReason
from django_apps.asteroid_lab.optimization.gene_projection import ProjectedGenePlacement
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput


@dataclass(frozen=True, slots=True)
class GeometryValidationResult:
    valid: bool
    reject_reason: CandidateRejectReason | None = None


def _coord_in_bbox(coord: Coord, inp: OptimizationInput) -> bool:
    sx, sy = coord
    bb = inp.route_domain_bbox
    return bb.min_sx <= sx <= bb.max_sx and bb.min_sy <= sy <= bb.max_sy


def _coord_valid_for_route_probe_start(coord: Coord, inp: OptimizationInput) -> bool:
    if not _coord_in_bbox(coord, inp):
        return False
    if coord in inp.mineable_cells or coord in inp.external_void_cells:
        return True
    return coord in {t.coord for t in inp.existing_transport_cells}


def validate_projected_gene_geometry(
    inp: OptimizationInput,
    projected: ProjectedGenePlacement,
) -> GeometryValidationResult:
    """Validate placement using ``OptimizationInput`` sets only (no cell.kind checks)."""

    if projected.extractor not in inp.rim_cells:
        return GeometryValidationResult(
            valid=False,
            reject_reason=CandidateRejectReason.EXTRACTOR_NOT_RIM,
        )

    occupied = projected.occupied_cells
    if len(occupied) != len(set(occupied)):
        return GeometryValidationResult(
            valid=False,
            reject_reason=CandidateRejectReason.PATTERN_OVERLAP_SELF,
        )

    for ext in projected.extensions:
        if ext not in inp.mineable_cells:
            return GeometryValidationResult(
                valid=False,
                reject_reason=CandidateRejectReason.EXTENSION_NOT_MINEABLE,
            )

    for cell in occupied:
        if cell not in inp.asteroid_cells:
            return GeometryValidationResult(
                valid=False,
                reject_reason=CandidateRejectReason.OCCUPIED_OUTSIDE_ASTEROID,
            )

    if projected.route_probe_start in occupied:
        return GeometryValidationResult(
            valid=False,
            reject_reason=CandidateRejectReason.OUTPUT_STUB_INSIDE_OCCUPIED,
        )

    if not _coord_valid_for_route_probe_start(projected.route_probe_start, inp):
        return GeometryValidationResult(
            valid=False,
            reject_reason=CandidateRejectReason.OUTPUT_STUB_INVALID_COORD,
        )

    return GeometryValidationResult(valid=True, reject_reason=None)
