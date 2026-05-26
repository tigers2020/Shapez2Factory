"""Read-only final_layout assert probe for E-track T1b investigation.

Mirrors assert order in final_validation.validate_final_layout without mutating production code.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput


class FinalLayoutAssertCode(StrEnum):
    FL_OK = "FL-OK"
    FL_01 = "FL-01"
    FL_02 = "FL-02"
    FL_03 = "FL-03"
    FL_04 = "FL-04"
    FL_05 = "FL-05"
    FL_06 = "FL-06"
    FL_07 = "FL-07"
    FL_08 = "FL-08"
    FL_09 = "FL-09"


def diagnose_final_layout(
    committed_ids: tuple[str, ...],
    reserved_route_cells: frozenset[Coord],
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
) -> tuple[FinalLayoutAssertCode, dict[str, Any]]:
    if not committed_ids:
        return FinalLayoutAssertCode.FL_01, {"committed_count": 0}

    occupied_seen: set[tuple[int, int]] = set()
    fot_seen: set[tuple[int, int]] = set()
    for candidate_id in committed_ids:
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            return FinalLayoutAssertCode.FL_02, {"candidate_id": candidate_id}

        overlap = candidate.occupied_cells & frozenset(occupied_seen)
        if overlap:
            return FinalLayoutAssertCode.FL_03, {
                "candidate_id": candidate_id,
                "overlap_coords": sorted(overlap),
            }

        fot_cell = fixed_output_transport_cell(candidate)
        if fot_cell in inp.mineable_cells:
            return FinalLayoutAssertCode.FL_04, {
                "candidate_id": candidate_id,
                "fot_cell": fot_cell,
            }

        fot_on_prior_occupied = fot_cell in occupied_seen
        occupied_on_prior_fot = bool(candidate.occupied_cells & frozenset(fot_seen))
        if fot_on_prior_occupied or occupied_on_prior_fot:
            return FinalLayoutAssertCode.FL_05, {
                "candidate_id": candidate_id,
                "fot_cell": fot_cell,
                "fot_on_prior_occupied": fot_on_prior_occupied,
                "occupied_on_prior_fot": occupied_on_prior_fot,
            }

        occupied_seen.update(candidate.occupied_cells)
        fot_seen.add(fot_cell)

        if candidate.output_stub not in reserved_route_cells and reserved_route_cells:
            return FinalLayoutAssertCode.FL_06, {
                "candidate_id": candidate_id,
                "output_stub": candidate.output_stub,
                "reserved_route_cells_nonempty": True,
            }

    reserved_vs_occupied = reserved_route_cells & frozenset(occupied_seen)
    if reserved_vs_occupied:
        return FinalLayoutAssertCode.FL_07, {
            "reserved_vs_occupied": sorted(reserved_vs_occupied),
        }

    for candidate_id in committed_ids:
        candidate = candidates_by_id[candidate_id]
        if not candidate.occupied_cells.issubset(inp.mineable_cells):
            outside = sorted(candidate.occupied_cells - inp.mineable_cells)
            return FinalLayoutAssertCode.FL_08, {
                "candidate_id": candidate_id,
                "outside_mineable_coords": outside,
            }
        if not candidate.reachable:
            return FinalLayoutAssertCode.FL_09, {"candidate_id": candidate_id}

    return FinalLayoutAssertCode.FL_OK, {"committed_count": len(committed_ids)}


__all__ = ["FinalLayoutAssertCode", "diagnose_final_layout"]
