"""Frozen golden_5x5_interior fixture for L4-1 greedy contract tests."""

from __future__ import annotations

from types import MappingProxyType

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import BundleCellRole
from shapez2_factory.application.asteroid_lab.layers.contracts.placement_state import (
    PlacementCommitState,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
    ProvisionalPlacedCell,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    LAYER_03_GREEDY_SOURCE,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import TransportKind
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map

GOLDEN_5X5_L3_EQUIPMENT_FOOTPRINT: frozenset[Coord] = frozenset(
    {
        (2, 3),
        (2, 4),
        (2, 5),
        (6, 3),
        (6, 4),
        (6, 5),
        (3, 2),
        (4, 2),
        (5, 2),
        (3, 6),
        (4, 6),
        (5, 6),
    }
)

GOLDEN_5X5_INTERIOR_CANDIDATES: frozenset[Coord] = frozenset(
    {
        (2, 2),
        (6, 2),
        (2, 6),
        (6, 6),
        (3, 3),
        (4, 3),
        (5, 3),
        (3, 4),
        (4, 4),
        (5, 4),
        (3, 5),
        (4, 5),
        (5, 5),
    }
)

# Void coord on golden map used only for witness-pollution overlay (not field equipment).
GOLDEN_5X5_WITNESS_VOID_STUB: Coord = (8, 4)


def golden_5x5_interior_complete_map() -> ReconstructionCompleteMap:
    return golden_5x5_complete_map()


def _placed_cell(coord: Coord, *, role: BundleCellRole) -> ProvisionalPlacedCell:
    return ProvisionalPlacedCell(
        coord=coord,
        candidate_id="golden_l3_fixture",
        placement_id="golden_l3_fixture",
        role=role,
        transport_kind=TransportKind.SPACE_BELT,
        placement_state=PlacementCommitState.PROVISIONAL_PLACED,
    )


def golden_5x5_interior_provisional_overlay() -> ProvisionalLayoutOverlay:
    """L3 rim equipment on field only — no transport stubs on field cells."""

    extractor = set(GOLDEN_5X5_L3_EQUIPMENT_FOOTPRINT)
    by_cell = {
        coord: _placed_cell(coord, role=BundleCellRole.MINER)
        for coord in GOLDEN_5X5_L3_EQUIPMENT_FOOTPRINT
    }
    return ProvisionalLayoutOverlay(
        occupied_cells=frozenset(extractor),
        extractor_cells=frozenset(extractor),
        extension_cells=frozenset(),
        transport_stub_cells=frozenset(),
        by_cell=MappingProxyType(by_cell),
        source_layer=LAYER_03_GREEDY_SOURCE,
    )


def golden_5x5_interior_witness_pollution_overlay() -> ProvisionalLayoutOverlay:
    """occupied_cells includes void witness stub not in extractor|extension."""

    base = golden_5x5_interior_provisional_overlay()
    witness = GOLDEN_5X5_WITNESS_VOID_STUB
    polluted_occupied = frozenset(set(base.occupied_cells) | {witness})
    by_cell = dict(base.by_cell)
    by_cell[witness] = _placed_cell(witness, role=BundleCellRole.TRANSPORT_STUB)
    return ProvisionalLayoutOverlay(
        occupied_cells=polluted_occupied,
        extractor_cells=base.extractor_cells,
        extension_cells=base.extension_cells,
        transport_stub_cells=frozenset({witness}),
        by_cell=MappingProxyType(by_cell),
        source_layer=LAYER_03_GREEDY_SOURCE,
    )


def golden_5x5_interior_extension_footprint_overlay() -> ProvisionalLayoutOverlay:
    """L3 equipment in extension_cells only (no extractor) — one interior cell blocked."""

    extension = frozenset({(4, 4)})
    by_cell = {coord: _placed_cell(coord, role=BundleCellRole.EXTENSION) for coord in extension}
    return ProvisionalLayoutOverlay(
        occupied_cells=extension,
        extractor_cells=frozenset(),
        extension_cells=extension,
        transport_stub_cells=frozenset(),
        by_cell=MappingProxyType(by_cell),
        source_layer=LAYER_03_GREEDY_SOURCE,
    )


def golden_5x5_interior_full_field_overlay() -> ProvisionalLayoutOverlay:
    """L3 footprint covers entire field — yields zero interior candidates."""

    field = golden_5x5_interior_complete_map().field_cells
    by_cell = {coord: _placed_cell(coord, role=BundleCellRole.MINER) for coord in field}
    return ProvisionalLayoutOverlay(
        occupied_cells=field,
        extractor_cells=field,
        extension_cells=frozenset(),
        transport_stub_cells=frozenset(),
        by_cell=MappingProxyType(by_cell),
        source_layer=LAYER_03_GREEDY_SOURCE,
    )


__all__ = [
    "GOLDEN_5X5_INTERIOR_CANDIDATES",
    "GOLDEN_5X5_L3_EQUIPMENT_FOOTPRINT",
    "GOLDEN_5X5_WITNESS_VOID_STUB",
    "golden_5x5_interior_complete_map",
    "golden_5x5_interior_extension_footprint_overlay",
    "golden_5x5_interior_full_field_overlay",
    "golden_5x5_interior_provisional_overlay",
    "golden_5x5_interior_witness_pollution_overlay",
]
