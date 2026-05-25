"""Track D+ PR-3 — CatalogPlacementSpec contract tests."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.catalog_candidate import (
    CatalogPlacementSpec,
    catalog_pattern_id,
    throughput_factor_for_footprint,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection


def test_throughput_factor_matches_pattern_library_table() -> None:
    assert throughput_factor_for_footprint(1) == 4
    assert throughput_factor_for_footprint(2) == 8
    assert throughput_factor_for_footprint(3) == 12
    assert throughput_factor_for_footprint(4) == 16
    assert throughput_factor_for_footprint(99) == 16


def test_catalog_pattern_id_never_lin_prefix() -> None:
    pid = catalog_pattern_id("bv:miner", CardinalDirection.N)
    assert pid.startswith("cat_")
    assert "lin_" not in pid
    assert pid == "cat_bv_miner_N"


def test_catalog_placement_spec_frozen() -> None:
    spec = CatalogPlacementSpec(
        canonical_id="bv:1",
        rotation=CardinalDirection.E,
        pattern_id="cat_bv_1_E",
        occupied_offsets=frozenset({(0, 0)}),
        fixed_output_transport_offset=(0, 0),
        output_stub_offset=(1, 0),
        output_dir="E",
        throughput_factor=4,
    )
    assert spec.topology_kind == "catalog"
