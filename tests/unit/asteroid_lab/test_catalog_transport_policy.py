"""T1 catalog default transport policy (Track B2)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.adapters.catalog_transport_policy import (
    CatalogTransportUnresolvedError,
    resolve_default_asteroid_transport_kind,
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
