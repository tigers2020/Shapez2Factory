"""Read-only final layout validation (RTTP Layer 4, PR-5)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput


def validate_final_layout(
    committed_ids: tuple[str, ...],
    reserved_route_cells: frozenset[Coord],
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
) -> bool:
    """Assert-only checks: disjoint occupied footprints; committed routes reserved."""

    if not committed_ids:
        return False

    occupied_seen: set[tuple[int, int]] = set()
    for candidate_id in committed_ids:
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            return False
        overlap = candidate.occupied_cells & frozenset(occupied_seen)
        if overlap:
            return False
        occupied_seen.update(candidate.occupied_cells)

        if candidate.output_stub not in reserved_route_cells and reserved_route_cells:
            return False

    reserved_vs_occupied = reserved_route_cells & frozenset(occupied_seen)
    if reserved_vs_occupied:
        return False

    for candidate_id in committed_ids:
        candidate = candidates_by_id[candidate_id]
        if not candidate.occupied_cells.issubset(inp.mineable_cells):
            return False
        if not candidate.reachable:
            return False

    return True


__all__ = ["validate_final_layout"]
