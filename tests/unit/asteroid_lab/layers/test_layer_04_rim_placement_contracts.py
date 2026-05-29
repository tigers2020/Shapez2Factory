"""Layer 04 v2 contract DTO tests."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.provisional_overlay import ProvisionalLayoutOverlay
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    Layer04PackingObservability,
    RimComponentSelectionRecord,
    RimPackingRejectionKind,
    RimPlacementRejection,
    RimPlacementRejectReason,
    RimSelectionStrategy,
    build_layer04_rim_placement_result,
)


def test_component_id_is_ordinal_string_only() -> None:
    rec = RimComponentSelectionRecord(
        component_id="component_0003",
        component_sort_key=(11, -6, "layer_03:miner:a"),
        node_count=5,
        selection_strategy=RimSelectionStrategy.EXACT_PACK,
        selected_candidate_ids=("a",),
        materialized_candidate_ids=("a",),
        total_effective_mining_gain=4,
        selected_count=1,
    )
    assert rec.component_id == "component_0003"


def test_packing_rejection_kind_enum_values() -> None:
    assert RimPackingRejectionKind.PACKING_SET_LOSER.value == "PACKING_SET_LOSER"


def test_rim_placement_rejection_accepts_packing_fields() -> None:
    rej = RimPlacementRejection(
        candidate_id="loser",
        equivalence_key="eq_loser",
        reason=RimPlacementRejectReason.PHYSICAL_OVERLAP,
        packing_component_id="component_0000",
        packing_rejection_kind=RimPackingRejectionKind.PACKING_SET_LOSER,
        winner_selected_due_to_higher_set_score=True,
        conflicting_candidate_id="winner",
    )
    assert rej.packing_rejection_kind is RimPackingRejectionKind.PACKING_SET_LOSER


def test_build_layer04_accepts_packing_observability() -> None:
    overlay = ProvisionalLayoutOverlay.empty()
    obs = Layer04PackingObservability(
        greedy_baseline_total_gain=10,
        selected_total_gain=12,
        budget_limited=False,
    )
    result = build_layer04_rim_placement_result(
        selected_placements=(),
        rejected_candidates=(),
        provisional_overlay=overlay,
        replay_frames=(),
        packing_observability=obs,
    )
    assert result.packing_observability is obs
    assert result.packing_observability.selected_total_gain == 12
