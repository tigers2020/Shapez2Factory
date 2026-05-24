"""BuildingCatalogSlice contract (Track B2)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
    SLICE_VERSION,
    VariantIdentity,
    catalog_slice_from_snapshot,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice_hash import (
    catalog_slice_hash,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    AsteroidGameDataSnapshot,
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    BuildingSnapshot,
    TransportRegistryEntry,
    build_snapshot_meta,
)


def _meta() -> object:
    return build_snapshot_meta(
        data_revision="rev",
        db_alias="default",
        built_at_utc="2026-05-24T00:00:00Z",
        content_hash="a" * 64,
        game_version="1.0",
    )


def test_catalog_slice_v2_includes_variant_geometries() -> None:
    snap = AsteroidGameDataSnapshot(
        meta=_meta(),  # type: ignore[arg-type]
        buildings=(
            BuildingSnapshot(
                canonical_id="bv:z",
                internal_name="z",
                footprint_cells=(BuildingFootprintCell(1, 2, 0),),
                connectors=(
                    BuildingConnectorSnapshot(
                        0,
                        "item_input",
                        "East",
                        "Regular",
                        0,
                        0,
                        0,
                    ),
                ),
            ),
            BuildingSnapshot(
                canonical_id="bv:a",
                internal_name="a",
                footprint_cells=(),
                connectors=(),
            ),
        ),
        transport_registry=(TransportRegistryEntry("z_kind", "belt", "bv:a"),),
    )
    sl = catalog_slice_from_snapshot(snap)
    assert sl.slice_version == SLICE_VERSION
    assert sl.transport_registry[0].transport_kind == "z_kind"
    assert sl.variants == (
        VariantIdentity("bv:a", "a"),
        VariantIdentity("bv:z", "z"),
    )
    assert len(sl.variant_geometries) == 2
    z = next(g for g in sl.variant_geometries if g.canonical_id == "bv:z")
    assert z.footprint_cells == (BuildingFootprintCell(1, 2, 0),)
    assert len(z.connectors) == 1
    assert catalog_slice_hash(sl) != catalog_slice_hash(
        BuildingCatalogSlice(
            slice_version=sl.slice_version,
            transport_registry=sl.transport_registry,
            variants=sl.variants,
            variant_geometries=(),
        )
    )


def test_catalog_slice_sorts_variants_and_registry() -> None:
    snap = AsteroidGameDataSnapshot(
        meta=_meta(),  # type: ignore[arg-type]
        buildings=(
            BuildingSnapshot("bv:b", "b", (), ()),
            BuildingSnapshot("bv:a", "a", (), ()),
        ),
        transport_registry=(
            TransportRegistryEntry("z", "belt", "bv:a"),
            TransportRegistryEntry("a", "belt", "bv:b"),
        ),
    )
    sl = catalog_slice_from_snapshot(snap)
    assert [v.internal_name for v in sl.variants] == ["a", "b"]
    assert [e.transport_kind for e in sl.transport_registry] == ["a", "z"]
