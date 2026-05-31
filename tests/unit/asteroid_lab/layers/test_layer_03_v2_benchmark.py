"""Layer 03 v2 ??E1 determinism + E2 L3-rim-only golden benchmark metrics.

Spec E (rim-only benchmark, NOT a 1:1 golden_map_result match ??that needs L4-L6, out of
scope): routed rim throughput, committed rim placement count, route-feasible output count,
``invalid_overlap_count == 0``, and a stable deterministic output hash. The full origin->result
golden equivalence is intentionally excluded here.
"""

from __future__ import annotations

import hashlib

from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedEntry,
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)

_THROUGHPUT_BY_GENE = {"m3e": 16, "m0e": 4}


def _catalog() -> GeneticSampleSeedSnapshot:
    return GeneticSampleSeedSnapshot(
        schema_version="genetic_sample_seed_v1",
        generated_at="",
        provenance_hash="",
        source_batch_id="",
        deterministic_sort_key="by_gene_id_then_throughput_desc",
        entries=(
            GeneticSampleSeedEntry(
                gene_id="m3e",
                resource_kind="shape",
                canonical_output_dir="E",
                occupied_offsets=((0, 0), (-1, 0), (-2, 0), (-3, 0)),
                extractor_offset=(0, 0),
                extension_offsets=((-1, 0), (-2, 0), (-3, 0)),
                output_stub_offset=(1, 0),
                route_probe_start_offset=(2, 0),
                throughput_factor=16,
                topology_signature_base="m3e_base",
            ),
            GeneticSampleSeedEntry(
                gene_id="m0e",
                resource_kind="both",
                canonical_output_dir="E",
                occupied_offsets=((0, 0),),
                extractor_offset=(0, 0),
                extension_offsets=(),
                output_stub_offset=(1, 0),
                route_probe_start_offset=(2, 0),
                throughput_factor=4,
                topology_signature_base="m0e_base",
            ),
        ),
    )


def _run() -> IntegratedRimGreedyResult:
    return run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        genetic_sample_seeds=_catalog(),
    )


def _output_hash(result: IntegratedRimGreedyResult) -> str:
    parts: list[str] = []
    for placement in result.committed_placements:
        parts.append(
            "|".join(
                [
                    placement.placement_id,
                    str(placement.anchor),
                    placement.output_dir,
                    str(sorted(placement.miner_cells)),
                    str(sorted(placement.extension_cells)),
                    str(placement.m_output_stub),
                    str(placement.route_probe_path),
                ]
            )
        )
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def test_l3_v2_output_is_deterministic_e1() -> None:
    first = _run()
    second = _run()
    assert [p.placement_id for p in first.committed_placements] == [
        p.placement_id for p in second.committed_placements
    ]
    assert first.reserved_route_cells == second.reserved_route_cells
    assert first.occupied_equipment_cells == second.occupied_equipment_cells
    assert _output_hash(first) == _output_hash(second)


def test_l3_rim_only_benchmark_metrics_e2() -> None:
    result = _run()
    committed = result.committed_placements

    # committed rim placement count: at least one route-feasible rim bundle.
    assert result.metrics.committed_placement_count == len(committed) >= 1

    # routed rim throughput = sum of committed gene throughputs (golden: m3e only -> 16).
    routed_rim_throughput = sum(_THROUGHPUT_BY_GENE[p.seed_id] for p in committed)
    assert routed_rim_throughput == 16

    # route-feasible output count == committed count (each survived commit-time re-probe).
    assert all(p.route_probe_path for p in committed)
    assert sum(1 for p in committed if p.route_probe_path[-1]) == len(committed)

    # invalid_overlap_count == 0: committed equipment footprints are pairwise disjoint.
    seen: set[tuple[int, int]] = set()
    overlap = 0
    for placement in committed:
        cells = set(placement.miner_cells) | set(placement.extension_cells)
        overlap += len(seen & cells)
        seen |= cells
    assert overlap == 0

    # deterministic output hash is stable.
    assert _output_hash(result) == _output_hash(_run())
