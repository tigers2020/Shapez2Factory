"""Read-only catalog footprint/connector policy (Track D; no game_data import)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.contracts.game_data_snapshot import BuildingFootprintCell


def summarize_footprint_catalog(catalog_slice: BuildingCatalogSlice) -> dict[str, int]:
    """Aggregate geometry counts for output-only RTTP metrics."""

    geometries = catalog_slice.variant_geometries
    return {
        "catalog_variant_geometry_count": len(geometries),
        "catalog_footprint_cell_count": sum(len(g.footprint_cells) for g in geometries),
        "catalog_connector_count": sum(len(g.connectors) for g in geometries),
    }


def footprint_cells_for_variant(
    canonical_id: str,
    *,
    catalog_slice: BuildingCatalogSlice,
) -> tuple[BuildingFootprintCell, ...]:
    """Return relative footprint cells for one variant, or empty when unknown."""

    for geometry in catalog_slice.variant_geometries:
        if geometry.canonical_id == canonical_id:
            return geometry.footprint_cells
    return ()


__all__ = [
    "footprint_cells_for_variant",
    "summarize_footprint_catalog",
]
