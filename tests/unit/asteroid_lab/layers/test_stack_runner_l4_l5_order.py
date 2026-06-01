"""Stack runner runs L4 inner fill before L5 transport routing."""

from __future__ import annotations

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
    LAYER_05_TRANSPORT_ROUTING,
    LAYERS_02_TO_06_ACTIVE,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.stack_status import StackRunStatus
from shapez2_factory.application.asteroid_lab.stack_runner import (
    LAYER_STACK_BUDGET_MS,
    _LayerStackRunner,
    run_layers_02_to_06,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)


def test_active_stack_order_fill_before_transport() -> None:
    assert list(LAYERS_02_TO_06_ACTIVE) == [
        "layer_02_exterior_transport",
        "layer_03_rim_greedy_placement",
        "layer_04_inner_pattern_fill",
        "layer_05_transport_routing",
        "layer_06_commit_validate",
    ]


def test_stack_runs_l4_fill_before_l5_transport() -> None:
    order: list[str] = []

    def stub_l2(**_kwargs: object) -> ExteriorConnectionPlan:
        return minimal_l2_plan_for_golden()

    def stub_l3(**_kwargs: object) -> object:
        from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
            GeneticSampleSeedSnapshot,
        )
        from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (  # noqa: E501
            run_layer_03_rim_greedy_placement,
        )

        seeds = GeneticSampleSeedSnapshot.from_payload(
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
        return run_layer_03_rim_greedy_placement(
            complete_map=golden_5x5_complete_map(),
            budget_ctx=LayerBudgetContext.from_budget_ms(LAYER_STACK_BUDGET_MS, now_fn=lambda: 0.0),
            exterior_plan=minimal_l2_plan_for_golden(),
            genetic_sample_seeds=seeds,
        )

    def track_l4(**_kwargs: object) -> object:
        from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (  # noqa: E501
            run_layer_04_inner_pattern_fill,
        )

        order.append(LAYER_04_INNER_PATTERN_FILL)
        return run_layer_04_inner_pattern_fill(**_kwargs)

    def track_l5(**_kwargs: object) -> object:
        from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.run import (  # noqa: E501
            run_layer_05_transport_routing,
        )

        order.append(LAYER_05_TRANSPORT_ROUTING)
        return run_layer_05_transport_routing(**_kwargs)

    def stub_l6(**_kwargs: object) -> None:
        return None

    runners = (
        _LayerStackRunner(LAYER_02_EXTERIOR_TRANSPORT, stub_l2),
        _LayerStackRunner(LAYER_03_RIM_GREEDY_PLACEMENT, stub_l3),
        _LayerStackRunner(LAYER_04_INNER_PATTERN_FILL, track_l4),
        _LayerStackRunner(LAYER_05_TRANSPORT_ROUTING, track_l5),
        _LayerStackRunner("layer_06_commit_validate", stub_l6),
    )
    core = run_layers_02_to_06(
        complete_map=golden_5x5_complete_map(),
        budget_ctx=LayerBudgetContext.from_budget_ms(LAYER_STACK_BUDGET_MS, now_fn=lambda: 0.0),
        runners=runners,
    )
    assert core.stack_result.status == StackRunStatus.SUCCESS
    assert order == [LAYER_04_INNER_PATTERN_FILL, LAYER_05_TRANSPORT_ROUTING]
    l5_summary = next(s for s in core.layer_summaries if s.layer_slug == LAYER_05_TRANSPORT_ROUTING)
    assert l5_summary.metrics.get("route_count") is not None
