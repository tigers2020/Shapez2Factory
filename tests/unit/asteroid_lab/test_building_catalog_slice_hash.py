"""catalog_slice_hash determinism (Track B2)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
    VariantIdentity,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice_hash import (
    catalog_slice_hash,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import TransportRegistryEntry


def test_catalog_slice_hash_includes_slice_version_and_order_invariant() -> None:
    t1 = TransportRegistryEntry("a", "belt", "bv:1")
    t2 = TransportRegistryEntry("z", "belt", "bv:2")
    v1 = VariantIdentity("bv:1", "a")
    v2 = VariantIdentity("bv:2", "z")
    s1 = BuildingCatalogSlice(SLICE_VERSION, (t2, t1), (v2, v1), ())
    s2 = BuildingCatalogSlice(SLICE_VERSION, (t1, t2), (v1, v2), ())
    h1 = catalog_slice_hash(s1)
    h2 = catalog_slice_hash(s2)
    assert h1 == h2
    assert len(h1) == 64


def test_different_slice_version_changes_hash() -> None:
    t = TransportRegistryEntry("a", "belt", "bv:1")
    s_v1 = BuildingCatalogSlice("building_catalog_slice_v1", (t,), (), ())
    s_other = BuildingCatalogSlice("building_catalog_slice_v0", (t,), (), ())
    assert catalog_slice_hash(s_v1) != catalog_slice_hash(s_other)
