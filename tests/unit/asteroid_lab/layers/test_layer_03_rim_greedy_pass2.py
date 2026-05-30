"""Pass2 scoring and variant winner selection."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.traversal_variants import (
    VARIANT_IDS,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)


def test_winning_variant_has_highest_score_then_lexicographic_id() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
    )
    assert result.winning_variant_id in VARIANT_IDS
    assert result.pass2_report.variant_id == result.winning_variant_id
    assert result.pass2_report.hard_fail is False
    assert result.pass2_report.score is not None
    assert result.metrics.pass2_score == result.pass2_report.score


def test_provisional_overlay_uses_greedy_source() -> None:
    from django_apps.asteroid_lab.layers.contracts.rim_greedy import LAYER_03_GREEDY_SOURCE

    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
    )
    assert result.provisional_overlay.source_layer == LAYER_03_GREEDY_SOURCE
    assert result.provisional_overlay.occupied_cells == frozenset(
        result.provisional_overlay.by_cell.keys()
    )
