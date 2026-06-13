"""Stack continues through L4 when L3 skeleton returns algorithm_reset."""

from __future__ import annotations

from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.stack_status import StackRunStatus
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    ALGORITHM_STUB_ID,
    run_layer_03_rim_greedy_placement,
)
from shapez2_factory.application.asteroid_lab.stack_runner import (
    LAYER_STACK_BUDGET_MS,
    _LayerStackRunner,
    run_layers_02_to_06,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)


def _stub_layer02(**_kwargs: object) -> ExteriorConnectionPlan:
    return minimal_l2_plan_for_golden()


def _nonempty_gene_catalog() -> GeneticSampleSeedSnapshot:
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


def _stub_layer04_fill(**_kwargs: object) -> object:
    from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (  # noqa: E501
        run_layer_04_inner_pattern_fill,
    )

    return run_layer_04_inner_pattern_fill(**_kwargs)


def test_stack_runner_accepts_empty_l3_and_reaches_l4() -> None:
    complete_map = golden_5x5_complete_map()
    budget_ctx = LayerBudgetContext.from_budget_ms(LAYER_STACK_BUDGET_MS, now_fn=lambda: 0.0)
    runners = (
        _LayerStackRunner(LAYER_02_EXTERIOR_TRANSPORT, _stub_layer02),
        _LayerStackRunner(LAYER_03_RIM_GREEDY_PLACEMENT, run_layer_03_rim_greedy_placement),
        _LayerStackRunner(LAYER_04_INNER_PATTERN_FILL, _stub_layer04_fill),
    )
    core = run_layers_02_to_06(
        complete_map=complete_map,
        budget_ctx=budget_ctx,
        runners=runners,
        genetic_sample_seeds=_nonempty_gene_catalog(),
    )
    assert core.stack_result.status == StackRunStatus.SUCCESS
    assert LAYER_03_RIM_GREEDY_PLACEMENT in core.stack_result.completed_layer_slugs
    assert LAYER_04_INNER_PATTERN_FILL in core.stack_result.completed_layer_slugs
    l3_summary = next(
        s for s in core.layer_summaries if s.layer_slug == LAYER_03_RIM_GREEDY_PLACEMENT
    )
    assert l3_summary.metrics.get("layer_skip_reason") == Layer03SkipReason.ALGORITHM_RESET.value
    assert l3_summary.metrics.get("committed_placement_count") == 0
    assert l3_summary.metrics.get("algorithm_stub") == ALGORITHM_STUB_ID
