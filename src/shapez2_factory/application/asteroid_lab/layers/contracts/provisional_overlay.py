"""Ephemeral provisional occupancy overlay (L4 output; L5/L6 input)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import BundleCellRole
from shapez2_factory.application.asteroid_lab.layers.contracts.placement_state import (
    PlacementCommitState,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import TransportKind
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

LAYER_04_SOURCE = "layer_04_rim_bundle_placement"


@dataclass(frozen=True, slots=True)
class ProvisionalPlacedCell:
    coord: Coord
    candidate_id: str
    placement_id: str
    role: BundleCellRole
    transport_kind: TransportKind
    placement_state: PlacementCommitState


@dataclass(frozen=True, slots=True)
class ProvisionalLayoutOverlay:
    occupied_cells: frozenset[Coord]
    extractor_cells: frozenset[Coord]
    extension_cells: frozenset[Coord]
    transport_stub_cells: frozenset[Coord]
    by_cell: Mapping[Coord, ProvisionalPlacedCell]
    source_layer: str = LAYER_04_SOURCE

    def __post_init__(self) -> None:
        if frozenset(self.by_cell.keys()) != self.occupied_cells:
            msg = "by_cell keys must equal occupied_cells"
            raise ValueError(msg)
        object.__setattr__(self, "by_cell", MappingProxyType(dict(self.by_cell)))

    @classmethod
    def empty(cls) -> ProvisionalLayoutOverlay:
        return cls(
            occupied_cells=frozenset(),
            extractor_cells=frozenset(),
            extension_cells=frozenset(),
            transport_stub_cells=frozenset(),
            by_cell=MappingProxyType({}),
        )


__all__ = [
    "LAYER_04_SOURCE",
    "ProvisionalLayoutOverlay",
    "ProvisionalPlacedCell",
]
