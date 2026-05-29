"""Layer 03 / 04 skeleton entrypoints (post reset)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.run import (
    run_layer_03_rim_mining_bundles,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
    empty_layer04_rim_placement_result,
    run_layer_04_rim_bundle_placement,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_candidate_set_factory import (
    rim_bundle_candidate_set_for_test,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)


def test_layer03_stub_returns_empty_pool() -> None:
    result = run_layer_03_rim_mining_bundles(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert result.normal_candidates == ()
    assert result.metrics.normal_candidate_count == 0


def test_layer04_stub_returns_empty_placement() -> None:
    result = run_layer_04_rim_bundle_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        candidate_set=rim_bundle_candidate_set_for_test(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert result == empty_layer04_rim_placement_result()
    assert result.selected_count == 0
