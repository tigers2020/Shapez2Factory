"""Layer 3 — rim mining bundle candidate expansion."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import RimBundleCandidateSet
from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.transport_kind import ResourceKind
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.expand import (
    expand_rim_bundle_candidates,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_catalog import (
    MinerSeedCatalog,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap


def run_layer_03_rim_mining_bundles(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext,
    seed_catalog: MinerSeedCatalog | None = None,
    resource_kind: ResourceKind | None = None,
) -> RimBundleCandidateSet:
    return expand_rim_bundle_candidates(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        budget_ctx=budget_ctx,
        seed_catalog=seed_catalog,
        resource_kind=resource_kind,
    )


__all__ = ["run_layer_03_rim_mining_bundles"]
