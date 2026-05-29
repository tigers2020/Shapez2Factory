"""Layer 04 v2 packing observability contract tests."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select_v2 import (
    select_non_overlapping_candidates_v2,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def test_observability_keeps_logical_winner_when_budget_blocks_materialization() -> None:
    first = succeeded_probe_at((0, 0), gene_key="aaa", equivalence_key="aaa")
    second = succeeded_probe_at((10, 0), gene_key="bbb", equivalence_key="bbb")
    outcome = select_non_overlapping_candidates_v2(
        normal_candidates=(first, second),
        budget_ctx=LayerBudgetContext.from_budget_ms(0),
    )

    records = outcome.packing_observability.component_records
    assert outcome.selected_entries == ()
    assert outcome.packing_observability.budget_limited is True
    assert len(records) == 2
    assert records[0].selected_candidate_ids == (first.candidate.candidate_id,)
    assert records[0].materialized_candidate_ids == ()
