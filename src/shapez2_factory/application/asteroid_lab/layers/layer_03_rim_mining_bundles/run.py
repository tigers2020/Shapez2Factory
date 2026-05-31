"""Layer 3 legacy entry — delegates to rim greedy placement."""

from __future__ import annotations

import warnings

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import ResourceKind
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def run_layer_03_rim_mining_bundles(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext,
    seed_catalog: object | None = None,
    resource_kind: ResourceKind | None = None,
) -> IntegratedRimGreedyResult:
    warnings.warn(
        "layer_03_rim_mining_bundles is deprecated; use layer_03_rim_greedy_placement",
        DeprecationWarning,
        stacklevel=2,
    )
    return run_layer_03_rim_greedy_placement(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        budget_ctx=budget_ctx,
        seed_catalog=seed_catalog,
        resource_kind=resource_kind,
    )


__all__ = ["run_layer_03_rim_mining_bundles"]
