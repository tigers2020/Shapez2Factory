"""Layer 03 rim greedy append contracts (committed placements → appended cells)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

LAYER_03_APPEND_SOURCE = LAYER_03_RIM_GREEDY_PLACEMENT


class AppendCellKind(StrEnum):
    MINER = "MINER"
    EXTENSION = "EXTENSION"
    OUTPUT_STUB = "OUTPUT_STUB"
    ROUTE_RESERVED = "ROUTE_RESERVED"


# v0: single cell per coord; higher index wins on collapse (see append mapper Task B).
APPEND_CELL_KIND_PRIORITY: tuple[AppendCellKind, ...] = (
    AppendCellKind.MINER,
    AppendCellKind.EXTENSION,
    AppendCellKind.OUTPUT_STUB,
    AppendCellKind.ROUTE_RESERVED,
)


@dataclass(frozen=True, slots=True)
class AppendedPlacementCell:
    coord: Coord
    kind: AppendCellKind
    placement_id: str
    variant_id: str
    source_layer: str


@dataclass(frozen=True, slots=True)
class Layer03AppendResult:
    cells: tuple[AppendedPlacementCell, ...]
    placement_count: int
    route_reserved_cell_count: int
    source_layer: str


def build_empty_layer03_append_result() -> Layer03AppendResult:
    return Layer03AppendResult(
        cells=(),
        placement_count=0,
        route_reserved_cell_count=0,
        source_layer=LAYER_03_APPEND_SOURCE,
    )


def _append_cell(
    coord: Coord,
    kind: AppendCellKind,
    placement: object,
) -> AppendedPlacementCell:
    from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
        CommittedRimSeedPlacement,
    )

    if not isinstance(placement, CommittedRimSeedPlacement):
        msg = "placement must be CommittedRimSeedPlacement"
        raise TypeError(msg)
    return AppendedPlacementCell(
        coord=coord,
        kind=kind,
        placement_id=placement.placement_id,
        variant_id=placement.variant_id,
        source_layer=LAYER_03_APPEND_SOURCE,
    )


def rebuild_append_result_from_committed(
    committed: tuple[object, ...],
    reserved_route: frozenset[Coord],
) -> Layer03AppendResult:
    """Rebuild append cells when only committed placements survived wire round-trip."""

    from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
        CommittedRimSeedPlacement,
    )

    typed_committed = tuple(
        p for p in committed if isinstance(p, CommittedRimSeedPlacement)
    )
    cells: list[AppendedPlacementCell] = []
    for placement in typed_committed:
        for coord in sorted(placement.miner_cells):
            cells.append(_append_cell(coord, AppendCellKind.MINER, placement))
        for coord in sorted(placement.extension_cells):
            cells.append(_append_cell(coord, AppendCellKind.EXTENSION, placement))
        cells.append(_append_cell(placement.m_output_stub, AppendCellKind.OUTPUT_STUB, placement))
    equipment = {
        coord
        for placement in typed_committed
        for coord in (*placement.miner_cells, *placement.extension_cells, placement.m_output_stub)
    }
    for coord in sorted(reserved_route - equipment):
        cells.append(
            AppendedPlacementCell(
                coord=coord,
                kind=AppendCellKind.ROUTE_RESERVED,
                placement_id="route_reserved",
                variant_id="route_reserved",
                source_layer=LAYER_03_APPEND_SOURCE,
            )
        )
    return Layer03AppendResult(
        cells=tuple(cells),
        placement_count=len(typed_committed),
        route_reserved_cell_count=len(reserved_route - equipment),
        source_layer=LAYER_03_APPEND_SOURCE,
    )


__all__ = [
    "APPEND_CELL_KIND_PRIORITY",
    "AppendCellKind",
    "AppendedPlacementCell",
    "LAYER_03_APPEND_SOURCE",
    "Layer03AppendResult",
    "build_empty_layer03_append_result",
    "rebuild_append_result_from_committed",
]
