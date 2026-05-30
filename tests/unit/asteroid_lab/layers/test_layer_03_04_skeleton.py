"""Layer 03 / 04 entrypoints."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer04_disabled import LAYER04_DISABLED_REASON
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.rim_greedy import IntegratedRimGreedyResult
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
    run_layer_04_rim_bundle_placement,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)


def test_layer03_greedy_returns_integrated_result() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert isinstance(result, IntegratedRimGreedyResult)
    assert len(result.committed_placements) >= 1
    assert result.metrics.committed_placement_count == len(result.committed_placements)
    assert result.winning_variant_id
    assert result.pass2_report.hard_fail is False


def test_layer04_shim_returns_disabled() -> None:
    result = run_layer_04_rim_bundle_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        candidate_set=None,  # type: ignore[arg-type]
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert result.status == "DISABLED"
    assert result.reason == LAYER04_DISABLED_REASON
    assert result.provisional_overlay.occupied_cells == frozenset()
