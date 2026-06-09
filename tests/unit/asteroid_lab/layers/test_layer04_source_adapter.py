"""Layer 04 source adapter tests (PR-L4-0)."""

from __future__ import annotations

from dataclasses import replace

from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
    RimGreedyMetrics,
    build_empty_integrated_rim_greedy_result,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.source_adapter import (  # noqa: E501
    build_layer04_sources,
    throughput_factor_to_source_load_m,
)


def _minimal_rim_result():
    placement = CommittedRimSeedPlacement(
        placement_id="p1",
        variant_id="v1",
        anchor=(0, 0),
        output_dir="E",
        seed_id="gene_a",
        miner_cells=frozenset({(0, 0)}),
        extension_cells=frozenset(),
        m_output_stub=(1, 0),
        throughput_factor=16,
        route_probe_path=((1, 0), (2, 0), (3, 0)),
    )
    return replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(placement,),
        occupied_equipment_cells=frozenset({(0, 0)}),
        metrics=RimGreedyMetrics(committed_placement_count=1),
    )


def test_source_load_m_maps_throughput_factor_to_lane_m_units() -> None:
    views = build_layer04_sources(_minimal_rim_result())
    assert len(views) == 1
    assert views[0].throughput_factor == 16
    assert views[0].source_load_m == throughput_factor_to_source_load_m(16) == 1


def test_throughput_factor_lane_mapping_table() -> None:
    assert throughput_factor_to_source_load_m(4) == 1
    assert throughput_factor_to_source_load_m(8) == 1
    assert throughput_factor_to_source_load_m(12) == 1
    assert throughput_factor_to_source_load_m(16) == 1


def test_equipment_cells_union_miner_and_extension() -> None:
    views = build_layer04_sources(_minimal_rim_result())
    assert views[0].equipment_cells == frozenset({(0, 0)})


def test_route_probe_path_preserved_as_witness() -> None:
    views = build_layer04_sources(_minimal_rim_result())
    assert views[0].route_probe_path == ((1, 0), (2, 0), (3, 0))
