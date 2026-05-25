"""Unit tests for ``asteroid_transport_projection`` (Phase A Task 2)."""

from __future__ import annotations

from django_apps.asteroid_lab.catalog.asteroid_transport_projection import (
    is_factory_internal_variant,
    placement_transport_canonical_ids,
    resolve_route_tile,
)
from django_apps.asteroid_lab.catalog.projection_compat_metrics import (
    reset_projection_compat_instrumentation,
)
from django_apps.asteroid_lab.catalog.projection_source import (
    ProjectionSourceKind,
    count_temporary_compat,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.contracts.game_data_snapshot import TransportRegistryEntry
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from tests.unit.asteroid_lab.test_catalog_placement_validation import _slice_with_variant


def test_is_factory_internal_variant_suffix() -> None:
    reset_projection_compat_instrumentation()

    assert is_factory_internal_variant("BeltDefaultForwardInternalVariant") is True
    assert is_factory_internal_variant("Layout_ShapeMiner") is False


def test_placement_transport_canonical_ids_excludes_internal_belt() -> None:
    sl = _slice_with_variant(
        canonical_id="bv:internal",
        internal_name="BeltDefaultForwardInternalVariant",
    )
    sl = BuildingCatalogSlice(
        slice_version=sl.slice_version,
        transport_registry=(
            TransportRegistryEntry("ForwardBelt", "belt", "bv:internal"),
        ),
        variants=sl.variants,
        variant_geometries=sl.variant_geometries,
    )
    allowed = placement_transport_canonical_ids(sl, TransportKind.SHAPE_BELT)
    assert "bv:internal" not in allowed


def test_resolve_route_tile_straight_forward_compat() -> None:
    tile = resolve_route_tile(
        transport_kind=TransportKind.SHAPE_BELT,
        incoming_dir=0,
        outgoing_dir=0,
    )
    assert tile.layout_t == "SpaceBelt_Forward"
    assert tile.source_kind is ProjectionSourceKind.TEMPORARY_COMPAT


def test_resolve_route_tile_left_turn_compat() -> None:
    # Dirs 0=E,1=S,2=W,3=N; (incoming+3)%4==outgoing => LeftTurn (same as overlay PR-1b).
    tile = resolve_route_tile(
        transport_kind=TransportKind.SHAPE_BELT,
        incoming_dir=0,
        outgoing_dir=3,
    )
    assert tile.layout_t == "SpaceBelt_LeftTurn"
    assert tile.source_kind is ProjectionSourceKind.TEMPORARY_COMPAT


def test_resolve_route_tile_includes_stub_footprint() -> None:
    tile = resolve_route_tile(
        transport_kind=TransportKind.SHAPE_BELT,
        incoming_dir=0,
        outgoing_dir=0,
    )
    assert len(tile.footprint_cells) == 1


def test_count_temporary_compat_from_dto_list() -> None:
    tile = resolve_route_tile(
        transport_kind=TransportKind.SHAPE_BELT,
        incoming_dir=0,
        outgoing_dir=3,
    )
    assert count_temporary_compat((tile,)) == 1
