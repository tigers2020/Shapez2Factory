"""Asteroid field cell accessors for reconstruction-complete terrain SoT."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.transport_kind import TransportKind
from shapez2_factory.domain.asteroid_lab.reconstruction.resource_kinds import (
    detect_present_resource_kinds,
    detect_primary_resource_kind as _detect_primary_resource_kind,
)


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

    return _detect_primary_resource_kind(complete_map)


def total_asteroid_field_cell_count(complete_map: ReconstructionCompleteMap) -> int:
    """All reconstruction-complete ``asteroid_*_field`` cells (shape + fluid)."""

    return len(complete_map.field_cells)


def asteroid_field_cell_count_for_placement(
    complete_map: ReconstructionCompleteMap,
    transport_kind: TransportKind,
) -> int:
    """Installable platform slots for ``transport_kind`` on reconstruction-complete map."""

    if transport_kind == TransportKind.SHAPE_BELT:
        return complete_map.shape_field_cell_count
    if transport_kind == TransportKind.FLUID_PIPE:
        return complete_map.fluid_field_cell_count
    return len(complete_map.field_cells)


__all__ = [
    "asteroid_field_cell_count_for_placement",
    "asteroid_field_cells_from_complete_map",
    "count_asteroid_field_cells_by_resource",
    "detect_present_resource_kinds",
    "detect_primary_resource_kind",
    "total_asteroid_field_cell_count",
]
