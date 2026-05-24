"""Shared minimal BuildingCatalogSlice for unit tests (Track D+ PR-3)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
    VariantGeometryCatalog,
    VariantIdentity,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    TransportRegistryEntry,
)


def build_minimal_test_catalog_slice(
    *,
    canonical_id: str = "bv:1",
) -> BuildingCatalogSlice:
    footprint = (
        BuildingFootprintCell(0, 0, 0),
        BuildingFootprintCell(1, 0, 1),
    )
    connectors = (BuildingConnectorSnapshot(0, "output", "East", "Regular", 1, 0, 0),)
    return BuildingCatalogSlice(
        slice_version=SLICE_VERSION,
        transport_registry=(TransportRegistryEntry("space_belt", "belt", canonical_id),),
        variants=(VariantIdentity(canonical_id, "miner"),),
        variant_geometries=(VariantGeometryCatalog(canonical_id, "miner", footprint, connectors),),
    )


__all__ = ["build_minimal_test_catalog_slice"]
