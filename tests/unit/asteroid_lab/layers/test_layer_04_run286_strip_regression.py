"""Run #286 strip component regression (greedy baseline vs v2 selection)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.rim_placement import RimSelectionStrategy
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.conflict_graph import (
    occupied_cells_for_entry,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select_v2 import (
    select_non_overlapping_candidates_v2,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_run286_strip import (
    load_run286_strip_probes,
)


def test_run286_strip_component_beats_greedy_baseline() -> None:
    entries = load_run286_strip_probes()
    assert len(entries) >= 10
    outcome = select_non_overlapping_candidates_v2(
        normal_candidates=entries,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
    )
    obs = outcome.packing_observability
    assert obs.greedy_baseline_total_gain is not None
    assert obs.selected_total_gain >= obs.greedy_baseline_total_gain
    assert len(obs.component_records) == 1
    assert obs.component_records[0].selection_strategy is RimSelectionStrategy.GREEDY_FALLBACK
    assert obs.component_records[0].node_count == len(entries)


def test_run286_strip_selected_set_is_non_overlapping() -> None:
    entries = load_run286_strip_probes()
    outcome = select_non_overlapping_candidates_v2(
        normal_candidates=entries,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
    )
    occupied_list = [occupied_cells_for_entry(e) for e in outcome.selected_entries]
    for i, left in enumerate(occupied_list):
        for right in occupied_list[i + 1 :]:
            assert left.isdisjoint(right)
