"""Track D+ PR-3 — build_catalog_placement_specs tests."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_candidate_placements import (
    build_catalog_placement_specs,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
    VariantGeometryCatalog,
    VariantIdentity,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    TransportRegistryEntry,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def _slice_with_output() -> BuildingCatalogSlice:
    footprint = (BuildingFootprintCell(0, 0, 0), BuildingFootprintCell(1, 0, 1))
    connectors = (BuildingConnectorSnapshot(0, "output", "East", "Regular", 1, 0, 0),)
    return BuildingCatalogSlice(
        slice_version=SLICE_VERSION,
        transport_registry=(TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        variants=(VariantIdentity("bv:1", "Layout_ShapeMiner"),),
        variant_geometries=(
            VariantGeometryCatalog("bv:1", "Layout_ShapeMiner", footprint, connectors),
        ),
    )


def test_build_specs_four_rotations_deterministic() -> None:
    specs = build_catalog_placement_specs(
        _slice_with_output(),
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert len(specs) == 4
    rotations = [s.rotation for s in specs]
    assert rotations == [
        CardinalDirection.E,
        CardinalDirection.N,
        CardinalDirection.S,
        CardinalDirection.W,
    ]
    assert all(s.pattern_id.startswith("cat_") for s in specs)
    assert all(s.throughput_factor == 4 for s in specs)


def test_build_specs_fluid_transport_uses_fluid_miner_not_shape_slice() -> None:
    sl = _slice_with_output()
    specs = build_catalog_placement_specs(sl, transport_kind=TransportKind.FLUID_PIPE)
    assert len(specs) == 4
    assert all("FluidMiner" in s.canonical_id for s in specs)
    assert all("InternalVariant" not in s.canonical_id for s in specs)


def test_build_catalog_placement_specs_excludes_internal_belt_variant() -> None:
    from tests.unit.asteroid_lab.test_catalog_placement_validation import _slice_with_variant

    sl = _slice_with_variant(
        canonical_id="bv:internal",
        internal_name="BeltDefaultForwardInternalVariant",
    )
    specs = build_catalog_placement_specs(sl, transport_kind=TransportKind.SHAPE_BELT)
    assert specs
    assert all("InternalVariant" not in s.canonical_id for s in specs)
    assert all("InternalVariant" not in s.pattern_id for s in specs)
    assert all(s.canonical_id.startswith(("bv:", "canon_manual:")) for s in specs)
