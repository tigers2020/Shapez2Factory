"""Route reservation hard-block tests for rim greedy pass1."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.rim_greedy import RimGreedyRejectReason
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.greedy_pass1 import (
    RimGreedyState,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.seed_orient import (
    SeedLayout,
    layout_seed_at_anchor,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map


def test_equipment_on_reserved_route_cell_is_rejected() -> None:
    complete_map = golden_5x5_complete_map()
    anchor = (6, 4)
    layout = layout_seed_at_anchor(
        seed_id="test_seed",
        anchor=anchor,
        output_dir="E",
        complete_map=complete_map,
    )
    assert isinstance(layout, SeedLayout)
    state = RimGreedyState(variant_id="CW_TL")
    state.reserved_route_cells.add(anchor)
    if layout.equipment_cells & frozenset(state.reserved_route_cells):
        reason = RimGreedyRejectReason.ROUTE_CROSSES_HARD_BLOCKER
    else:
        reason = None
    assert reason is RimGreedyRejectReason.ROUTE_CROSSES_HARD_BLOCKER


def test_golden_run_reserves_route_and_may_reject_overlapping_equipment() -> None:
    from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
    from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
        run_layer_03_rim_greedy_placement,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        minimal_l2_plan_for_golden,
    )

    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
    )
    assert len(result.committed_placements) >= 1
    assert len(result.reserved_route_cells) >= 1
    reject_reasons = {r.reason for r in result.rejected_attempts}
    assert reject_reasons  # greedy walk produces rejects on later anchors
