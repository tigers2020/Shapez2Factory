"""L4 mining-first greedy selection (corner W/S overlap)."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    RimPackingRejectionKind,
    RimPlacementRejectReason,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select import (
    select_non_overlapping_candidates,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select_v2 import (
    select_non_overlapping_candidates_v2,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.sort_keys import (
    effective_mining_gain,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_corner_ws_overlap import (
    corner_ws_s_probe,
    corner_ws_w_probe,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def test_l4_selects_higher_gain_s_over_w_on_overlap() -> None:
    w = corner_ws_w_probe()
    s = corner_ws_s_probe()
    assert effective_mining_gain(w.candidate) == 6
    assert effective_mining_gain(s.candidate) == 9
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    selected, rejected = select_non_overlapping_candidates(
        normal_candidates=(w, s),
        budget_ctx=ctx,
    )
    assert len(selected) == 1
    assert selected[0].candidate.candidate_id == s.candidate.candidate_id
    assert selected[0].candidate.output_dir is Direction.S
    assert len(rejected) == 1
    rej = rejected[0]
    assert rej.reason is RimPlacementRejectReason.PHYSICAL_OVERLAP
    assert rej.rejected_candidate_id == w.candidate.candidate_id
    assert rej.conflicting_candidate_id == s.candidate.candidate_id
    assert rej.conflicting_winner_output_dir == Direction.S.value
    assert rej.conflicting_winner_mining_cell_count == 9
    assert rej.winner_selected_due_to_higher_mining_gain is True


def test_v2_selects_higher_gain_s_over_w_with_packing_set_loser() -> None:
    w = corner_ws_w_probe()
    s = corner_ws_s_probe()
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    outcome = select_non_overlapping_candidates_v2(
        normal_candidates=(w, s),
        budget_ctx=ctx,
    )
    assert len(outcome.selected_entries) == 1
    assert outcome.selected_entries[0].candidate.candidate_id == s.candidate.candidate_id
    losers = [
        r
        for r in outcome.rejected
        if r.rejected_candidate_id == w.candidate.candidate_id
    ]
    assert len(losers) == 1
    rej = losers[0]
    assert rej.reason is RimPlacementRejectReason.PHYSICAL_OVERLAP
    assert rej.packing_rejection_kind is RimPackingRejectionKind.PACKING_SET_LOSER
    assert rej.winner_selected_due_to_higher_set_score is True
    assert rej.conflicting_winner_mining_cell_count == 9


def test_non_succeeded_probe_excluded_from_overlap_sort() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        RouteProbedBundleCandidate,
        RouteProbeStatus,
    )

    ok = succeeded_probe_at((1, 1))
    bad = RouteProbedBundleCandidate(
        candidate=ok.candidate,
        route_probe_status=RouteProbeStatus.FAILED,
        route_probe_result=None,
        route_goal_id=None,
        reject_reason=None,
    )
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    selected, rejected = select_non_overlapping_candidates(
        normal_candidates=(bad, ok),
        budget_ctx=ctx,
    )
    assert len(selected) == 1
    assert rejected[0].reason is RimPlacementRejectReason.NON_SUCCEEDED_PROBE
