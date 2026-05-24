"""Allowlist catalog slice extracted from ``AsteroidGameDataSnapshot`` (Track B2)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    AsteroidGameDataSnapshot,
    TransportRegistryEntry,
)

SLICE_VERSION = "building_catalog_slice_v1"


@dataclass(frozen=True, slots=True)
class VariantIdentity:
    canonical_id: str
    internal_name: str


@dataclass(frozen=True, slots=True)
class BuildingCatalogSlice:
    slice_version: str
    transport_registry: tuple[TransportRegistryEntry, ...]
    variants: tuple[VariantIdentity, ...]


def catalog_slice_from_snapshot(snapshot: AsteroidGameDataSnapshot) -> BuildingCatalogSlice:
    """Extract identity + transport registry only (no footprint/connectors on output)."""

    variants = tuple(
        VariantIdentity(canonical_id=b.canonical_id, internal_name=b.internal_name)
        for b in sorted(
            snapshot.buildings,
            key=lambda b: (b.internal_name, b.canonical_id),
        )
    )
    registry = tuple(sorted(snapshot.transport_registry, key=lambda e: e.transport_kind))
    return BuildingCatalogSlice(
        slice_version=SLICE_VERSION,
        transport_registry=registry,
        variants=variants,
    )


__all__ = [
    "SLICE_VERSION",
    "BuildingCatalogSlice",
    "VariantIdentity",
    "catalog_slice_from_snapshot",
]
