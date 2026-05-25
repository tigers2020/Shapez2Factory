"""Tests for ``miner_placement_topology`` normalization (Phase 1)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import cardinal_unit_vector
from django_apps.asteroid_lab.catalog.miner_placement_topology import (
    normalize_miner_placement_topology,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import VariantGeometryCatalog
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
)


def _geometry_two_cell_east_output() -> VariantGeometryCatalog:
    footprint = (
        BuildingFootprintCell(0, 0, 0),
        BuildingFootprintCell(1, 0, 1),
    )
    connectors = (BuildingConnectorSnapshot(0, "output", "East", "Regular", 1, 0, 0),)
    return VariantGeometryCatalog(
        canonical_id="bv:test_miner",
        internal_name="Layout_ShapeMiner",
        footprint_cells=footprint,
        connectors=connectors,
    )


def test_manual_two_cell_east_topology_phase1() -> None:
    topo = normalize_miner_placement_topology(
        _geometry_two_cell_east_output(),
        rotation=CardinalDirection.E,
    )
    assert topo is not None
    assert topo.extractor_offset == (0, 0)
    assert topo.fixed_output_transport_offset == (1, 0)
    assert topo.output_stub_offset == (2, 0)
    assert topo.extension_offsets == ()
    assert topo.occupied_offsets == frozenset({(0, 0)})
    assert topo.footprint_evidence == frozenset({(0, 0), (1, 0)})
    assert topo.throughput_factor == 4
    assert topo.output_dir == "E"


@pytest.mark.parametrize(
    ("rotation", "expected_fot", "expected_stub"),
    [
        (CardinalDirection.E, (1, 0), (2, 0)),
        (CardinalDirection.N, (0, -1), (0, -2)),
        (CardinalDirection.S, (0, 1), (0, 2)),
        (CardinalDirection.W, (-1, 0), (-2, 0)),
    ],
)
def test_rotation_matrix_invariants_nesw(
    rotation: CardinalDirection,
    expected_fot: tuple[int, int],
    expected_stub: tuple[int, int],
) -> None:
    topo = normalize_miner_placement_topology(
        _geometry_two_cell_east_output(),
        rotation=rotation,
    )
    assert topo is not None
    unit = cardinal_unit_vector(CardinalDirection(topo.output_dir))
    assert topo.fixed_output_transport_offset == expected_fot
    assert topo.output_stub_offset == expected_stub
    assert topo.fixed_output_transport_offset not in topo.occupied_offsets
    assert topo.output_stub_offset not in topo.occupied_offsets
    output_axis = (
        topo.extractor_offset[0] + unit[0],
        topo.extractor_offset[1] + unit[1],
    )
    assert output_axis not in topo.extension_offsets
    assert topo.output_stub_offset == (
        topo.fixed_output_transport_offset[0] + unit[0],
        topo.fixed_output_transport_offset[1] + unit[1],
    )


def test_ambiguous_extractor_candidates_returns_none() -> None:
    footprint = (
        BuildingFootprintCell(0, 0, 0),
        BuildingFootprintCell(2, 0, 1),
    )
    connectors = (BuildingConnectorSnapshot(0, "output", "East", "Regular", 1, 0, 0),)
    geometry = VariantGeometryCatalog(
        canonical_id="bv:ambiguous",
        internal_name="Layout_ShapeMiner",
        footprint_cells=footprint,
        connectors=connectors,
    )
    assert normalize_miner_placement_topology(geometry, rotation=CardinalDirection.E) is None
