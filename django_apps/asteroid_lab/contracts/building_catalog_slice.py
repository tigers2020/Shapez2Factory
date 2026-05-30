"""Shim: relocated to ``shapez2_factory.domain.asteroid_lab.building_catalog_slice`` (PR-CLI-2a).

Re-exports the pure core catalog slice DTOs so existing ``django_apps`` imports keep working.
Import the core module directly in new code.
"""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
    VariantGeometryCatalog,
    VariantIdentity,
    catalog_slice_from_snapshot,
)

__all__ = [
    "SLICE_VERSION",
    "BuildingCatalogSlice",
    "VariantGeometryCatalog",
    "VariantIdentity",
    "catalog_slice_from_snapshot",
]
