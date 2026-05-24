"""Track D — catalog footprint policy."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_footprint_policy import (
    footprint_cells_for_variant,
    summarize_footprint_catalog,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
    SLICE_VERSION,
    VariantGeometryCatalog,
    VariantIdentity,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingFootprintCell,
    TransportRegistryEntry,
)


def _slice_with_one_footprint() -> BuildingCatalogSlice:
    return BuildingCatalogSlice(
        slice_version=SLICE_VERSION,
        transport_registry=(TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        variants=(VariantIdentity("bv:1", "miner_a"),),
        variant_geometries=(
            VariantGeometryCatalog(
                canonical_id="bv:1",
                internal_name="miner_a",
                footprint_cells=(
                    BuildingFootprintCell(0, 0, 0),
                    BuildingFootprintCell(1, 0, 0),
                ),
                connectors=(),
            ),
        ),
    )


def test_summarize_footprint_catalog_counts() -> None:
    metrics = summarize_footprint_catalog(_slice_with_one_footprint())
    assert metrics == {
        "catalog_variant_geometry_count": 1,
        "catalog_footprint_cell_count": 2,
        "catalog_connector_count": 0,
    }


def test_footprint_cells_for_variant_lookup() -> None:
    cells = footprint_cells_for_variant("bv:1", catalog_slice=_slice_with_one_footprint())
    assert len(cells) == 2


def test_footprint_cells_for_variant_missing_returns_empty() -> None:
    assert footprint_cells_for_variant("missing", catalog_slice=_slice_with_one_footprint()) == ()
