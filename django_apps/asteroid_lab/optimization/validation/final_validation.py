"""Read-only final layout validation (RTTP Layer 4, PR-5)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.macros.macro_dtos import MacroBundleCandidate


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


def validate_macro_layout(
    committed_macro_ids: tuple[str, ...],
    committed_child_ids: tuple[str, ...],
    reserved_route_cells: frozenset[Coord],
    macros_by_id: dict[str, MacroBundleCandidate],
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
) -> bool:
    """Read-only macro layout checks after macro-only commit (RTTP v1 PR-H)."""

    if not committed_macro_ids:
        return False

    expected_children: list[str] = []
    for macro_id in committed_macro_ids:
        macro_row = macros_by_id.get(macro_id)
        if macro_row is None:
            return False
        expected_children.extend(child.candidate_id for child in macro_row.macro.children)

    if sorted(expected_children) != sorted(committed_child_ids):
        return False

    occupied_seen: set[Coord] = set()
    for child_id in committed_child_ids:
        candidate = candidates_by_id.get(child_id)
        if candidate is None:
            return False
        overlap = candidate.occupied_cells & frozenset(occupied_seen)
        if overlap:
            return False
        occupied_seen.update(candidate.occupied_cells)
        if not candidate.occupied_cells.issubset(inp.mineable_cells):
            return False
        if not candidate.reachable:
            return False

    return True


__all__ = ["validate_final_layout", "validate_macro_layout"]
