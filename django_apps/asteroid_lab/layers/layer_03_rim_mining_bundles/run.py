"""Layer 3 stub — PR-1 skeleton only."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap


def run_layer_03_rim_mining_bundles(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
) -> None:
    _ = complete_map
    _ = budget_ctx
