"""Shared projection DTOs — adapter view over game_data, not SoT."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import BuildingFootprintCell
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind

_INTERNAL_VARIANT_SUFFIX: Final[str] = "InternalVariant"

COMPAT_TRANSPORT_STUB_FOOTPRINT: Final[tuple[BuildingFootprintCell, ...]] = (
    BuildingFootprintCell(x=0, y=0, order_index=0),
)


def is_factory_internal_variant(internal_name: str) -> bool:
    """True when ``internal_name`` is a factory-only *InternalVariant* row."""

    return internal_name.endswith(_INTERNAL_VARIANT_SUFFIX)


class ProjectionSourceKind(StrEnum):
    GAME_DATA_CANON = "game_data_canon"
    TEMPORARY_COMPAT = "temporary_compat"
    CANON_MANUAL = "canon_manual"


@dataclass(frozen=True, slots=True)
class ProjectedTransportTile:
    layout_t: str
    transport_kind: TransportKind
    canonical_id: str | None
    footprint_cells: tuple[BuildingFootprintCell, ...]
    display_rotation_q: int
    source_kind: ProjectionSourceKind
    source_detail: str


@dataclass(frozen=True, slots=True)
class ProjectedSpriteRef:
    layout_t: str
    sprite_path: str
    canonical_id: str | None
    source_kind: ProjectionSourceKind
    source_detail: str


@dataclass(frozen=True, slots=True)
class ProjectedEquipmentSpec:
    layout_t: str
    canonical_id: str
    pattern_id: str
    rotation: CardinalDirection
    occupied_offsets: tuple[Coord, ...]
    output_stub_offset: Coord
    output_dir: CardinalDirection
    throughput_factor: int
    source_kind: ProjectionSourceKind
    source_detail: str


def count_temporary_compat(
    projected: Sequence[ProjectedTransportTile | ProjectedEquipmentSpec],
) -> int:
    """Count emitted projection rows using compat fallback (canonical run metric)."""

    return sum(1 for row in projected if row.source_kind is ProjectionSourceKind.TEMPORARY_COMPAT)


__all__ = [
    "COMPAT_TRANSPORT_STUB_FOOTPRINT",
    "ProjectionSourceKind",
    "ProjectedEquipmentSpec",
    "ProjectedSpriteRef",
    "ProjectedTransportTile",
    "count_temporary_compat",
    "is_factory_internal_variant",
]
