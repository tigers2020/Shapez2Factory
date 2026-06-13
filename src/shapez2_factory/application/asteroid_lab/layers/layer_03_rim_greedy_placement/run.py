"""Layer 3 skeleton — algorithm reset (empty integrated result)."""

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
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
    RimGreedyPolicy,
    build_empty_integrated_rim_greedy_result,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

ALGORITHM_STUB_ID = "algorithm_reset"


def run_layer_03_rim_greedy_placement(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext,
    seed_catalog: object | None = None,
    resource_kind: ResourceKind | None = None,
    transport_kind: TransportKind | None = None,
    policy: RimGreedyPolicy | None = None,
    genetic_sample_seeds: GeneticSampleSeedSnapshot | None = None,
) -> IntegratedRimGreedyResult:
    _ = (
        complete_map,
        exterior_plan,
        budget_ctx,
        seed_catalog,
        resource_kind,
        transport_kind,
        policy,
        genetic_sample_seeds,
    )
    return build_empty_integrated_rim_greedy_result(
        layer_skip_reason=Layer03SkipReason.ALGORITHM_RESET.value,
        rim_anchor_count=0,
    )


__all__ = ["ALGORITHM_STUB_ID", "run_layer_03_rim_greedy_placement"]
