"""Unit tests for S2b-1 extension topology synthesis."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import cardinal_unit_vector
from django_apps.asteroid_lab.catalog.extension_topology_synthesis import (
    ExtensionTopologyKind,
    synthesize_opposite_arm_linear_topologies,
    throughput_factor_for_topology,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
)
from django_apps.asteroid_lab.genetic_sample.gene_template import (
    throughput_factor_for_extension_count,
)
from tests.unit.asteroid_lab.test_catalog_placement_validation import _slice_with_variant

_EXTRACTOR: tuple[int, int] = (0, 0)


@pytest.fixture
def catalog_slice_with_shape_miner() -> object:
    footprint = (BuildingFootprintCell(0, 0, 0), BuildingFootprintCell(1, 0, 1))
    connectors = (BuildingConnectorSnapshot(0, "output", "East", "Regular", 1, 0, 0),)
    return _slice_with_variant(
        canonical_id="bv:shape_miner",
        internal_name="Layout_ShapeMiner",
        footprint=footprint,
        connectors=connectors,
    )


_CARDINALS = (
    CardinalDirection.E,
    CardinalDirection.N,
    CardinalDirection.S,
    CardinalDirection.W,
)


def test_e_output_opposite_arm_linear_offsets() -> None:
    topologies = synthesize_opposite_arm_linear_topologies(
        output_dir=CardinalDirection.E,
        max_extension_count=3,
    )
    assert len(topologies) == 4
    assert topologies[0].extension_count == 0
    assert topologies[0].topology_kind == ExtensionTopologyKind.NONE
    assert topologies[0].synthesis_arm == CardinalDirection.W
    assert topologies[1].extension_offsets == ((-1, 0),)
    assert topologies[3].extension_offsets == ((-1, 0), (-2, 0), (-3, 0))


def test_e_output_extension_not_on_output_axis() -> None:
    output_axis = cardinal_unit_vector(CardinalDirection.E)
    for topo in synthesize_opposite_arm_linear_topologies(output_dir=CardinalDirection.E):
        assert output_axis not in topo.extension_offsets


@pytest.mark.parametrize("output_dir", _CARDINALS)
def test_inv_r03_no_extension_on_output_forward_arm(output_dir: CardinalDirection) -> None:
    forbidden = (
        _EXTRACTOR[0] + cardinal_unit_vector(output_dir)[0],
        _EXTRACTOR[1] + cardinal_unit_vector(output_dir)[1],
    )
    for topo in synthesize_opposite_arm_linear_topologies(output_dir=output_dir):
        assert forbidden not in topo.extension_offsets


@pytest.mark.parametrize("output_dir", _CARDINALS)
def test_inv_r01_fot_and_stub_not_in_occupied(output_dir: CardinalDirection) -> None:
    unit = cardinal_unit_vector(output_dir)
    fot = (unit[0], unit[1])
    stub = (fot[0] + unit[0], fot[1] + unit[1])
    for topo in synthesize_opposite_arm_linear_topologies(output_dir=output_dir):
        occupied = frozenset({_EXTRACTOR, *topo.extension_offsets})
        assert fot not in occupied
        assert stub not in occupied


@pytest.mark.parametrize("output_dir", _CARDINALS)
def test_throughput_factors_match_extension_count(output_dir: CardinalDirection) -> None:
    topologies = synthesize_opposite_arm_linear_topologies(output_dir=output_dir)
    assert len(topologies) == 4
    expected = {4, 8, 12, 16}
    actual = {throughput_factor_for_topology(t) for t in topologies}
    assert actual == expected
    for topo in topologies:
        assert throughput_factor_for_topology(topo) == throughput_factor_for_extension_count(
            topo.extension_count
        )


def test_synthesis_returns_four_topologies_for_max_three() -> None:
    for output_dir in _CARDINALS:
        assert len(synthesize_opposite_arm_linear_topologies(output_dir=output_dir)) == 4


def test_manual_shape_miner_emits_four_specs_per_rotation(
    catalog_slice_with_shape_miner: object,
) -> None:
    from django_apps.asteroid_lab.catalog.asteroid_equipment_projection import (
        list_equipment_placement_specs,
    )
    from django_apps.asteroid_lab.optimization.input_contracts import TransportKind

    specs = list_equipment_placement_specs(
        catalog_slice_with_shape_miner,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    e_specs = [s for s in specs if s.rotation is CardinalDirection.E]
    assert len(e_specs) == 4
    assert {s.throughput_factor for s in e_specs} == {4, 8, 12, 16}
    assert all(
        s.pattern_id.endswith(f"_ext{n}")
        for n, s in enumerate(sorted(e_specs, key=lambda r: r.throughput_factor))
    )
    assert len(specs) == 16
