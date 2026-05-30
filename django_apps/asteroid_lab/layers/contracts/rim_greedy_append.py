"""Layer 03 rim greedy append contracts (committed placements → appended cells)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.layers.contracts.layer_slugs import LAYER_03_RIM_GREEDY_PLACEMENT
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

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


__all__ = [
    "APPEND_CELL_KIND_PRIORITY",
    "AppendCellKind",
    "AppendedPlacementCell",
    "LAYER_03_APPEND_SOURCE",
    "Layer03AppendResult",
    "build_empty_layer03_append_result",
]
