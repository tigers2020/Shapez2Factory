"""Catalog-native placement spec contracts (Track D+ PR-3)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.optimization.coords import Coord

_THROUGHPUT_BY_EXT: tuple[int, ...] = (4, 8, 12, 16)


def throughput_factor_for_footprint(cell_count: int) -> int:
    extension_count = min(3, max(0, cell_count - 1))
    return _THROUGHPUT_BY_EXT[extension_count]


def catalog_pattern_id(canonical_id: str, rotation: CardinalDirection) -> str:
    safe = canonical_id.replace(":", "_")
    return f"cat_{safe}_{rotation.value}"


@dataclass(frozen=True, slots=True)
class CatalogPlacementSpec:
    canonical_id: str
    rotation: CardinalDirection
    pattern_id: str
    extractor_offset: Coord
    extension_offsets: tuple[Coord, ...]
    fixed_output_transport_offset: Coord
    output_stub_offset: Coord
    occupied_offsets: frozenset[Coord]
    output_dir: str
    throughput_factor: int
    topology_kind: str = "catalog"


__all__ = [
    "CatalogPlacementSpec",
    "catalog_pattern_id",
    "throughput_factor_for_footprint",
]
