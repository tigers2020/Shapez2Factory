"""Layer 03 skip gate on missing/empty gene catalog (spec section M)."""

from __future__ import annotations

from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedEntry,
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)


def _budget_ctx() -> LayerBudgetContext:
    return LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)


def _present_catalog() -> GeneticSampleSeedSnapshot:
    return GeneticSampleSeedSnapshot.from_payload(
        {
            "schema_version": "genetic_sample_seed_v1",
            "generated_at": "2026-05-31T00:00:00Z",
            "provenance_hash": "abc123",
            "source_batch_id": "exhaustive_sample_gene_v1",
            "deterministic_sort_key": "by_gene_id_then_throughput_desc",
            "entries": [
                {
                    "gene_id": "m3e_01",
                    "resource_kind": "both",
                    "canonical_output_dir": "E",
                    "occupied_offsets": [[0, 0], [-1, 0], [-2, 0], [-3, 0]],
                    "extractor_offset": [0, 0],
                    "extension_offsets": [[-1, 0], [-2, 0], [-3, 0]],
                    "output_stub_offset": [1, 0],
                    "route_probe_start_offset": [2, 0],
                    "throughput_factor": 16,
                    "topology_signature_base": "m3e_01_base",
                }
            ],
        }
    )


def test_MISSING_GENETIC_SAMPLE_SEEDS_returns_skip() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=_budget_ctx(),
        genetic_sample_seeds=None,
    )
    assert result.committed_placements == ()
    assert result.metrics.layer_skip_reason == Layer03SkipReason.MISSING_GENETIC_SAMPLE_SEEDS.value


def test_empty_gene_catalog_returns_skip() -> None:
    snapshot = GeneticSampleSeedSnapshot.from_payload(
        {"schema_version": "genetic_sample_seed_v1", "entries": []}
    )
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=_budget_ctx(),
        genetic_sample_seeds=snapshot,
    )
    assert result.committed_placements == ()
    assert result.metrics.layer_skip_reason == Layer03SkipReason.MISSING_GENETIC_SAMPLE_SEEDS.value


def test_nonzero_extractor_offset_skips_with_invalid_snapshot_reason() -> None:
    bad_entry = GeneticSampleSeedEntry(
        gene_id="shifted_m",
        resource_kind="both",
        canonical_output_dir="E",
        occupied_offsets=((1, 0), (2, 0)),
        extractor_offset=(1, 0),
        extension_offsets=((2, 0),),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=4,
        topology_signature_base="shifted",
    )
    snapshot = GeneticSampleSeedSnapshot(
        schema_version="genetic_sample_seed_v1",
        generated_at="",
        provenance_hash="",
        source_batch_id="",
        deterministic_sort_key="",
        entries=(bad_entry,),
    )
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=_budget_ctx(),
        genetic_sample_seeds=snapshot,
    )
    assert result.committed_placements == ()
    assert (
        result.metrics.layer_skip_reason
        == Layer03SkipReason.INVALID_GENETIC_SAMPLE_SEED_SNAPSHOT.value
    )


def test_present_catalog_runs_v2_and_commits() -> None:
    # v2: a present gene catalog runs the real pipeline (no reset skip). On the golden
    # fixture the single aligned anchor (6,4) commits one route-feasible bundle.
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=_budget_ctx(),
        genetic_sample_seeds=_present_catalog(),
    )
    assert result.metrics.layer_skip_reason is None
    assert result.metrics.committed_placement_count == 1
    assert result.committed_placements[0].anchor == (6, 4)
