"""Unit tests for ``asteroid_equipment_projection`` (Phase A Task 3)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.catalog.asteroid_equipment_projection import (
    ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST,
    list_equipment_placement_specs,
)
from django_apps.asteroid_lab.catalog.projection_source import ProjectionSourceKind
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from tests.unit.asteroid_lab.test_catalog_placement_validation import _slice_with_variant


@pytest.fixture
def catalog_slice_with_shape_miner() -> object:
    footprint = (BuildingFootprintCell(0, 0, 0), BuildingFootprintCell(1, 0, 1))
    connectors = (
        BuildingConnectorSnapshot(0, "output", "East", "Regular", 1, 0, 0),
    )
    return _slice_with_variant(
        canonical_id="bv:shape_miner",
        internal_name="Layout_ShapeMiner",
        footprint=footprint,
        connectors=connectors,
    )


def test_allowlist_contains_layout_miners() -> None:
    assert "Layout_ShapeMiner" in ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST
    assert "Layout_FluidMiner" in ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST


def test_specs_never_use_internal_variant_canonical_id(
    catalog_slice_with_shape_miner,
) -> None:
    specs = list_equipment_placement_specs(
        catalog_slice_with_shape_miner,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert specs
    for spec in specs:
        assert "InternalVariant" not in spec.canonical_id
        assert "InternalVariant" not in spec.pattern_id
        assert spec.layout_t == "Layout_ShapeMiner"
        assert spec.source_kind is ProjectionSourceKind.GAME_DATA_CANON


def test_canon_manual_when_allowlisted_layout_missing_from_slice() -> None:
    sl = _slice_with_variant(
        canonical_id="bv:internal",
        internal_name="BeltDefaultForwardInternalVariant",
    )
    specs = list_equipment_placement_specs(sl, transport_kind=TransportKind.SHAPE_BELT)
    assert specs
    assert all(s.source_kind is ProjectionSourceKind.CANON_MANUAL for s in specs)
    assert all(s.layout_t == "Layout_ShapeMiner" for s in specs)
    assert all(isinstance(s.throughput_factor, int) for s in specs)
