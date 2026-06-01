"""Resource-kind detection on reconstruction-complete terrain (layer -1 / L1 handoff)."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

_PRESENT_ORDER: tuple[str, ...] = ("shape", "fluid")


def detect_present_resource_kinds(
    complete_map: ReconstructionCompleteMap,
) -> tuple[str, ...]:
    """Resources with at least one field cell; canonical order shape then fluid."""

    present: list[str] = []
    if complete_map.shape_field_cell_count > 0:
        present.append("shape")
    if complete_map.fluid_field_cell_count > 0:
        present.append("fluid")
    return tuple(present)


def detect_primary_resource_kind(complete_map: ReconstructionCompleteMap) -> str:
    """Dominant resource from field counts; tie → shape."""

    if complete_map.fluid_field_cell_count > complete_map.shape_field_cell_count:
        return "fluid"
    return "shape"


__all__ = [
    "detect_present_resource_kinds",
    "detect_primary_resource_kind",
]
