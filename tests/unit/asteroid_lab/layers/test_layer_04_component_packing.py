"""Layer 04 v2 component packing integration tests (§9.1–9.3)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.rim_placement import RimSelectionStrategy
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select_v2 import (
    select_non_overlapping_candidates_v2,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_large_component import (
    large_component_probes,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_packing_density import (
    packing_density_probes,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_tiebreak_sets import (
    tiebreak_count_component_probes,
    tiebreak_route_cost_component_probes,
)


def test_packing_density_selects_vertical_bundle_not_blocker() -> None:
    entries = packing_density_probes()
    outcome = select_non_overlapping_candidates_v2(
        normal_candidates=entries,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
    )
    selected_equiv = {e.candidate.equivalence_key for e in outcome.selected_entries}
    assert "blocker_a" not in selected_equiv
    assert selected_equiv == {
        "vert_0",
        "vert_1",
        "vert_3",
        "vert_4",
        "vert_5",
    }
    assert outcome.packing_observability.selected_total_gain == 25


def test_tiebreak_prefers_higher_selected_count_at_equal_gain() -> None:
    outcome = select_non_overlapping_candidates_v2(
        normal_candidates=tiebreak_count_component_probes(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
    )
    selected_equiv = {e.candidate.equivalence_key for e in outcome.selected_entries}
    assert selected_equiv == {"vert_0", "vert_2", "vert_4"}
    assert "blocker" not in selected_equiv
    assert outcome.packing_observability.selected_total_gain == 6


def test_tiebreak_prefers_lower_route_cost_in_two_node_component() -> None:
    outcome = select_non_overlapping_candidates_v2(
        normal_candidates=tiebreak_route_cost_component_probes(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
    )
    assert len(outcome.selected_entries) == 1
    assert outcome.selected_entries[0].candidate.equivalence_key == "cheap"
    assert outcome.packing_observability.selected_total_gain == 1


def test_large_component_uses_greedy_fallback() -> None:
    outcome = select_non_overlapping_candidates_v2(
        normal_candidates=large_component_probes(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
    )
    assert len(outcome.packing_observability.component_records) == 1
    rec = outcome.packing_observability.component_records[0]
    assert rec.selection_strategy is RimSelectionStrategy.GREEDY_FALLBACK
    assert rec.node_count == 21
    assert len(outcome.selected_entries) >= 1
