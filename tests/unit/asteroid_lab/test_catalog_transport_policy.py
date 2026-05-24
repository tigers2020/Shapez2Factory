"""T1 catalog default transport policy (Track B2)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.adapters.catalog_transport_policy import (
    CatalogTransportUnresolvedError,
    resolve_cell_transport_kind,
    resolve_default_asteroid_transport_kind,
    transport_kind_lookup_from_slice,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import TransportRegistryEntry
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def test_resolve_default_shape_belt_when_only_belt_category() -> None:
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        (),
    )
    assert resolve_default_asteroid_transport_kind(sl) is TransportKind.SHAPE_BELT


def test_resolve_default_shape_belt_when_belt_and_pipe_both_in_registry() -> None:
    """Pipe rows do not block asteroid greenfield default when belt channel exists."""

    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (
            TransportRegistryEntry("a", "belt", "bv:1"),
            TransportRegistryEntry("b", "pipe", "bv:2"),
        ),
        (),
    )
    assert resolve_default_asteroid_transport_kind(sl) is TransportKind.SHAPE_BELT


def test_resolve_default_fails_when_registry_empty() -> None:
    sl = BuildingCatalogSlice(SLICE_VERSION, (), ())
    with pytest.raises(CatalogTransportUnresolvedError):
        resolve_default_asteroid_transport_kind(sl)


def test_lookup_maps_registry_transport_kind_to_domain_kind() -> None:
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        (),
    )
    lk = transport_kind_lookup_from_slice(sl)
    assert lk["space_belt"] is TransportKind.SHAPE_BELT


def test_duplicate_registry_key_same_kind_last_wins() -> None:
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (
            TransportRegistryEntry("dup", "belt", "bv:1"),
            TransportRegistryEntry("dup", "belt", "bv:2"),
        ),
        (),
    )
    lk = transport_kind_lookup_from_slice(sl)
    assert lk["dup"] is TransportKind.SHAPE_BELT


def test_duplicate_registry_key_conflicting_kind_raises() -> None:
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (
            TransportRegistryEntry("dup", "belt", "bv:1"),
            TransportRegistryEntry("dup", "pipe", "bv:2"),
        ),
        (),
    )
    with pytest.raises(CatalogTransportUnresolvedError) as exc_info:
        transport_kind_lookup_from_slice(sl)
    assert "dup" in str(exc_info.value)


def test_resolve_cell_prefers_domain_enum_over_registry() -> None:
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (TransportRegistryEntry("shape_belt", "belt", "bv:1"),),
        (),
    )
    assert (
        resolve_cell_transport_kind("shape_belt", catalog_slice=sl)
        is TransportKind.SHAPE_BELT
    )


def test_resolve_cell_uses_registry_key_when_not_domain_enum() -> None:
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        (),
    )
    assert (
        resolve_cell_transport_kind("space_belt", catalog_slice=sl)
        is TransportKind.SHAPE_BELT
    )


def test_resolve_cell_without_catalog_returns_none_for_unknown() -> None:
    assert resolve_cell_transport_kind("space_belt", catalog_slice=None) is None


def test_resolve_cell_with_catalog_raises_when_unresolved() -> None:
    sl = BuildingCatalogSlice(SLICE_VERSION, (), ())
    with pytest.raises(CatalogTransportUnresolvedError) as exc_info:
        resolve_cell_transport_kind(
            "unknown_wire",
            catalog_slice=sl,
            coord=(4, 5),
        )
    assert "(4, 5)" in str(exc_info.value)
    assert "unknown_wire" in str(exc_info.value)
