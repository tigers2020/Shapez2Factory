"""Layer 3 — reset stub (algorithm removed; see 2026-05-31-layer-03-algorithm-reset-design)."""

from __future__ import annotations

from shapez2_factory.adapters.asteroid_lab.gene_catalog_snapshot import GeneCatalogSnapshot
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
    build_layer03_reset_observability_events,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

ALGORITHM_STUB_ID = "reset_stub_v1"


def run_layer_03_rim_greedy_placement(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext,
    seed_catalog: object | None = None,
    resource_kind: ResourceKind | None = None,
    transport_kind: TransportKind | None = None,
    policy: RimGreedyPolicy | None = None,
    gene_catalog: GeneCatalogSnapshot | None = None,
) -> IntegratedRimGreedyResult:
    _ = (
        complete_map,
        budget_ctx,
        seed_catalog,
        resource_kind,
        transport_kind,
        policy,
    )
    if exterior_plan is None:
        return build_empty_integrated_rim_greedy_result(
            layer_skip_reason=Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN.value,
            rim_anchor_count=0,
        )
    if gene_catalog is None or not gene_catalog.entries:
        return build_empty_integrated_rim_greedy_result(
            layer_skip_reason=Layer03SkipReason.MISSING_GENE_CATALOG.value,
            rim_anchor_count=0,
        )
    return build_empty_integrated_rim_greedy_result(
        layer_skip_reason=Layer03SkipReason.ALGORITHM_RESET.value,
        rim_anchor_count=0,
        observability_events=build_layer03_reset_observability_events(),
    )


__all__ = ["ALGORITHM_STUB_ID", "run_layer_03_rim_greedy_placement"]
