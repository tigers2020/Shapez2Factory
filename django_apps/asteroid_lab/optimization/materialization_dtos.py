"""Phase K — materialized transport layout DTOs (PR6)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import MaterializationFailureReason, TransportKind


@dataclass(frozen=True, slots=True)
class MaterializedTransportCell:
    """One belt/pipe cell on the dense Server X/Y grid."""

    coord: Coord
    tile_type: str
    transport_kind: TransportKind
    rotation: int = 0


@dataclass(frozen=True, slots=True)
class MaterializedLayoutCells:
    """Deterministically ordered transport cells from route materialization."""

    cells: tuple[MaterializedTransportCell, ...]


@dataclass(frozen=True, slots=True)
class RouteMaterializationResult:
    layout: MaterializedLayoutCells | None
    failure_reason: MaterializationFailureReason | None
