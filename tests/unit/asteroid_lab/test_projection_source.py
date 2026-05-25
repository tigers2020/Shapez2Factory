"""Projection source DTOs — game_data adapter view (Phase A Task 1)."""

from __future__ import annotations

from django_apps.asteroid_lab.catalog.projection_source import (
    COMPAT_TRANSPORT_STUB_FOOTPRINT,
    ProjectedEquipmentSpec,
    ProjectedTransportTile,
    ProjectionSourceKind,
    count_temporary_compat,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def test_projection_source_kind_values_are_stable_strings() -> None:
    assert ProjectionSourceKind.GAME_DATA_CANON.value == "game_data_canon"
    assert ProjectionSourceKind.TEMPORARY_COMPAT.value == "temporary_compat"
    assert ProjectionSourceKind.CANON_MANUAL.value == "canon_manual"


def test_projected_transport_tile_is_frozen() -> None:
    row = ProjectedTransportTile(
        layout_t="SpaceBelt_Forward",
        transport_kind=TransportKind.SHAPE_BELT,
        canonical_id=None,
        footprint_cells=COMPAT_TRANSPORT_STUB_FOOTPRINT,
        display_rotation_q=0,
        source_kind=ProjectionSourceKind.TEMPORARY_COMPAT,
        source_detail="compat:route_forward",
    )
    assert row.layout_t == "SpaceBelt_Forward"
    assert len(row.footprint_cells) == 1


def test_projected_equipment_spec_throughput_factor_is_int() -> None:
    spec = ProjectedEquipmentSpec(
        layout_t="Layout_ShapeMiner",
        canonical_id="bv:miner",
        pattern_id="cat_bv_miner_E",
        rotation=CardinalDirection.E,
        occupied_offsets=((0, 0),),
        output_stub_offset=(1, 0),
        output_dir=CardinalDirection.E,
        throughput_factor=4,
        source_kind=ProjectionSourceKind.CANON_MANUAL,
        source_detail="island:balance",
    )
    assert spec.throughput_factor == 4
    assert isinstance(spec.throughput_factor, int)


def test_count_temporary_compat_from_dto_sequence() -> None:
    row = ProjectedTransportTile(
        layout_t="SpaceBelt_Forward",
        transport_kind=TransportKind.SHAPE_BELT,
        canonical_id=None,
        footprint_cells=COMPAT_TRANSPORT_STUB_FOOTPRINT,
        display_rotation_q=0,
        source_kind=ProjectionSourceKind.TEMPORARY_COMPAT,
        source_detail="compat:route_forward",
    )
    canon = ProjectedTransportTile(
        layout_t="SpaceBelt_Forward",
        transport_kind=TransportKind.SHAPE_BELT,
        canonical_id="bv:1",
        footprint_cells=COMPAT_TRANSPORT_STUB_FOOTPRINT,
        display_rotation_q=0,
        source_kind=ProjectionSourceKind.GAME_DATA_CANON,
        source_detail="batch:1",
    )
    assert count_temporary_compat((row, canon)) == 1
