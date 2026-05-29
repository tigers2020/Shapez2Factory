"""Layer 3 stub — rim mining bundle candidate pool (rebuild from skeleton)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import (
    Layer03ExpansionMetrics,
    RimBundleCandidateSet,
    build_rim_bundle_candidate_set,
)
from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.layer03_observability import (
    build_layer03_observability,
)
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.transport_kind import ResourceKind
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap


def _empty_candidate_set() -> RimBundleCandidateSet:
    metrics = Layer03ExpansionMetrics.empty()
    return build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=metrics,
        observability=build_layer03_observability(metrics=metrics, normal_candidates=()),
    )


def run_layer_03_rim_mining_bundles(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext,
    seed_catalog: object | None = None,
    resource_kind: ResourceKind | None = None,
) -> RimBundleCandidateSet:
    _ = (complete_map, exterior_plan, budget_ctx, seed_catalog, resource_kind)
    return _empty_candidate_set()


__all__ = ["run_layer_03_rim_mining_bundles"]
