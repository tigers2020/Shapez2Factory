"""Legacy L3 slug delegates to rim greedy with deprecation."""

from __future__ import annotations

import warnings

from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.layer_slugs import LAYER_03_RIM_GREEDY_PLACEMENT
from django_apps.asteroid_lab.layers.contracts.rim_greedy import IntegratedRimGreedyResult
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.run import (
    run_layer_03_rim_mining_bundles,
)

pytest_plugins = ["tests.unit.asteroid_lab.layers.test_layer_03_rim_greedy_run"]


def test_legacy_l3_delegates_to_greedy(
    canonical_complete_map,
    budget_ctx: LayerBudgetContext,
) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = run_layer_03_rim_mining_bundles(
            complete_map=canonical_complete_map,
            exterior_plan=None,
            budget_ctx=budget_ctx,
        )
    assert isinstance(result, IntegratedRimGreedyResult)
    assert result.metrics.canonical_layer_slug == LAYER_03_RIM_GREEDY_PLACEMENT
    assert any(issubclass(item.category, DeprecationWarning) for item in caught)
