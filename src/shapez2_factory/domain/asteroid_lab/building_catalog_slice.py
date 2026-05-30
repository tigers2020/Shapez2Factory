"""Allowlist catalog slice extracted from ``AsteroidGameDataSnapshot`` (Track B2 / D)."""

from __future__ import annotations

from dataclasses import dataclass

from shapez2_factory.domain.asteroid_lab.game_data_snapshot import (
    AsteroidGameDataSnapshot,
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    TransportRegistryEntry,
    validate_building_snapshot,
)

SLICE_VERSION = "building_catalog_slice_v2"


@dataclass(frozen=True, slots=True)
class VariantIdentity:
    canonical_id: str
    internal_name: str


@dataclass(frozen=True, slots=True)
class VariantGeometryCatalog:
    canonical_id: str
    internal_name: str
    footprint_cells: tuple[BuildingFootprintCell, ...]
    connectors: tuple[BuildingConnectorSnapshot, ...]


@dataclass(frozen=True, slots=True)
class BuildingCatalogSlice:
    slice_version: str
    transport_registry: tuple[TransportRegistryEntry, ...]
    variants: tuple[VariantIdentity, ...]
    variant_geometries: tuple[VariantGeometryCatalog, ...]


def catalog_slice_from_snapshot(snapshot: AsteroidGameDataSnapshot) -> BuildingCatalogSlice:
    """Extract identity, transport registry, and per-variant geometry for the allowlist slice."""

    buildings = tuple(
        validate_building_snapshot(b)
        for b in sorted(
            snapshot.buildings,
            key=lambda b: (b.internal_name, b.canonical_id),
        )
    )
    variants = tuple(
        VariantIdentity(canonical_id=b.canonical_id, internal_name=b.internal_name)
        for b in buildings
    )
    variant_geometries = tuple(
        VariantGeometryCatalog(
            canonical_id=b.canonical_id,
            internal_name=b.internal_name,
            footprint_cells=b.footprint_cells,
            connectors=b.connectors,
        )
        for b in buildings
    )
    registry = tuple(sorted(snapshot.transport_registry, key=lambda e: e.transport_kind))
    return BuildingCatalogSlice(
        slice_version=SLICE_VERSION,
        transport_registry=registry,
        variants=variants,
        variant_geometries=variant_geometries,
    )


__all__ = [
    "SLICE_VERSION",
    "BuildingCatalogSlice",
    "VariantGeometryCatalog",
    "VariantIdentity",
    "catalog_slice_from_snapshot",
]
