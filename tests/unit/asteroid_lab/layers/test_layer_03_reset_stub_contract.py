"""Layer 03 v2 run contract - deterministic provisional placement (spec 2026-05-31 v2)."""

from __future__ import annotations

from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    RimGreedyObservationPhase,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from shapez2_factory.application.asteroid_lab.layers.observability.post_summary_metrics import (
    build_layer03_rim_greedy_post_summary_metrics,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)


def _present_gene_catalog() -> GeneticSampleSeedSnapshot:
    return GeneticSampleSeedSnapshot.from_payload(
        {
            "schema_version": "genetic_sample_seed_v1",
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


def test_layer_03_v2_commits_provisional_placement_with_present_catalog() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        genetic_sample_seeds=_present_gene_catalog(),
    )
    assert result.metrics.committed_placement_count == 1
    assert result.metrics.layer_skip_reason is None
    assert result.pass2_report.hard_fail is False
    phases = {e.phase for e in result.observability_events}
    assert RimGreedyObservationPhase.RIM_GREEDY_BEGIN in phases
    assert RimGreedyObservationPhase.RIM_SEED_COMMITTED in phases
    assert RimGreedyObservationPhase.RIM_GREEDY_COMPLETE in phases
    summary = build_layer03_rim_greedy_post_summary_metrics(result)
    # algorithm_stub is reset-specific; a real v2 placement run reports no reset stub.
    assert summary["algorithm_stub"] is None
    assert summary["layer_skip_reason"] is None
    assert summary["committed_placement_count"] == 1


def test_layer_03_missing_exterior_plan_uses_enum_skip_not_reset() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=None,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert result.metrics.layer_skip_reason == Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN
