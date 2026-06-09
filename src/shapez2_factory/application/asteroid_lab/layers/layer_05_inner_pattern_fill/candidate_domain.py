"""L4 interior candidate domain (pure, testable)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def l3_authoritative_equipment_footprint(
    provisional_overlay: ProvisionalLayoutOverlay,
) -> frozenset[Coord]:
    """Field equipment only — excludes transport stubs and route probe witnesses."""

    return provisional_overlay.extractor_cells | provisional_overlay.extension_cells


def compute_interior_candidates(
    *,
    complete_map: ReconstructionCompleteMap,
    provisional_overlay: ProvisionalLayoutOverlay,
) -> frozenset[Coord]:
    footprint = l3_authoritative_equipment_footprint(provisional_overlay)
    return complete_map.field_cells - footprint


def sorted_interior_candidates(candidates: frozenset[Coord]) -> tuple[Coord, ...]:
    return tuple(sorted(candidates, key=lambda c: (c[0], c[1])))


__all__ = [
    "compute_interior_candidates",
    "l3_authoritative_equipment_footprint",
    "sorted_interior_candidates",
]
