"""Asteroid field cell accessors for reconstruction-complete terrain SoT."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap


def asteroid_field_cells_from_complete_map(
    complete_map: ReconstructionCompleteMap,
) -> frozenset[tuple[int, int]]:
    """All island-local field coords from a complete map (no overlay reads)."""

    return complete_map.field_cells


def count_asteroid_field_cells_by_resource(
    complete_map: ReconstructionCompleteMap,
) -> dict[str, int]:
    """Count shape/fluid field cells on the complete map."""

    return {
        "shape": complete_map.shape_field_cell_count,
        "fluid": complete_map.fluid_field_cell_count,
    }


def detect_primary_resource_kind(complete_map: ReconstructionCompleteMap) -> str:
    """Dominant asteroid resource from complete map field counts; tie → shape."""

    if complete_map.fluid_field_cell_count > complete_map.shape_field_cell_count:
        return "fluid"
    return "shape"


__all__ = [
    "asteroid_field_cells_from_complete_map",
    "count_asteroid_field_cells_by_resource",
    "detect_primary_resource_kind",
]
