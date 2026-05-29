"""Layer 04 v2 select_v2 budget and baseline isolation."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.rim_placement import RimPackingRejectionKind
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select_v2 import (
    OBSERVABILITY_BASELINE_BUDGET_MS,
    compute_greedy_baseline_observability,
    select_non_overlapping_candidates_v2,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def test_greedy_baseline_uses_fresh_budget_context() -> None:
    runtime = LayerBudgetContext.from_budget_ms(60_000)
    before = runtime.remaining_budget_ms()
    a = succeeded_probe_at((0, 0), equivalence_key="a")
    b = succeeded_probe_at((10, 10), equivalence_key="b")
    gain, skip = compute_greedy_baseline_observability(
        normal_candidates=(a, b),
        observability_budget_ms=OBSERVABILITY_BASELINE_BUDGET_MS,
    )
    assert gain is not None
    assert skip is None
    assert runtime.remaining_budget_ms() == before


def test_select_v2_budget_interrupt_marks_observability() -> None:
    a = succeeded_probe_at((0, 0), equivalence_key="a")
    b = succeeded_probe_at((5, 0), equivalence_key="b")
    runtime = LayerBudgetContext.from_budget_ms(0)
    outcome = select_non_overlapping_candidates_v2(
        normal_candidates=(a, b),
        budget_ctx=runtime,
    )
    assert outcome.selected_entries == ()
    assert outcome.packing_observability.budget_limited is True
    assert any(
        r.packing_rejection_kind is RimPackingRejectionKind.BUDGET_INTERRUPTED
        for r in outcome.rejected
    )


def test_packing_set_loser_on_exact_pack_component() -> None:
    low = succeeded_probe_at(
        (0, 0),
        equivalence_key="low",
        output_dir=Direction.W,
        mining=frozenset({(0, 0)}),
        transport=frozenset({(9, 9)}),
    )
    high = succeeded_probe_at(
        (0, 0),
        equivalence_key="high",
        output_dir=Direction.E,
        mining=frozenset({(0, 0), (1, 0), (2, 0)}),
        transport=frozenset({(9, 8)}),
    )
    outcome = select_non_overlapping_candidates_v2(
        normal_candidates=(low, high),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
    )
    assert len(outcome.selected_entries) == 1
    assert outcome.selected_entries[0].candidate.equivalence_key == "high"
    losers = [
        r
        for r in outcome.rejected
        if r.packing_rejection_kind is RimPackingRejectionKind.PACKING_SET_LOSER
    ]
    assert len(losers) == 1
    assert losers[0].packing_component_id == "component_0000"
