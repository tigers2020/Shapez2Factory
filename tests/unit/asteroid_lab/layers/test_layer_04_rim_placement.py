"""Layer 04 rim bundle provisional placement tests (PR-3c)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.layers.contracts.candidates import (
    Layer03ExpansionMetrics,
    build_rim_bundle_candidate_set,
)
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.placement_state import PlacementCommitState
from django_apps.asteroid_lab.layers.contracts.provisional_overlay import ProvisionalLayoutOverlay
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    Layer04RimPlacementResult,
    RimPlacementRejectReason,
    build_layer04_rim_placement_result,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.place import (
    build_rim_bundle_placement,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.replay import (
    build_layer04_replay_frames,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
    run_layer_04_rim_bundle_placement,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select import (
    select_non_overlapping_candidates,
)
from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED,
    EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN,
    EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE,
    is_registered_event_type,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def test_placement_commit_state_provisional_value() -> None:
    assert PlacementCommitState.PROVISIONAL_PLACED.value == "PROVISIONAL_PLACED"
    assert PlacementCommitState.ROUTED_CONFIRMED.value == "ROUTED_CONFIRMED"


def test_provisional_overlay_empty() -> None:
    overlay = ProvisionalLayoutOverlay.empty()
    assert overlay.occupied_cells == frozenset()
    assert dict(overlay.by_cell) == {}
    assert overlay.source_layer == "layer_04_rim_bundle_placement"


def test_provisional_overlay_post_init_rejects_by_cell_mismatch() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import BundleCellRole
    from django_apps.asteroid_lab.layers.contracts.provisional_overlay import ProvisionalPlacedCell

    coord = (3, 4)
    cell = ProvisionalPlacedCell(
        coord=coord,
        candidate_id="c1",
        placement_id="c1:prov",
        role=BundleCellRole.MINER,
        transport_kind=TransportKind.SHAPE_BELT,
        placement_state=PlacementCommitState.PROVISIONAL_PLACED,
    )
    with pytest.raises(ValueError, match="by_cell keys must equal occupied_cells"):
        ProvisionalLayoutOverlay(
            occupied_cells=frozenset(),
            extractor_cells=frozenset({coord}),
            extension_cells=frozenset(),
            transport_stub_cells=frozenset(),
            by_cell={coord: cell},
        )


def test_layer04_result_selected_count_matches_placements() -> None:
    overlay = ProvisionalLayoutOverlay.empty()
    with pytest.raises(ValueError, match="selected_count"):
        Layer04RimPlacementResult(
            selected_placements=(),
            rejected_candidates=(),
            selected_count=1,
            rejected_overlap_count=0,
            rejected_budget_count=0,
            provisional_overlay=overlay,
            replay_frames=(),
        )


def test_build_layer04_rim_placement_result_sets_counts() -> None:
    overlay = ProvisionalLayoutOverlay.empty()
    result = build_layer04_rim_placement_result(
        selected_placements=(),
        rejected_candidates=(),
        provisional_overlay=overlay,
        replay_frames=(),
    )
    assert result.selected_count == 0
    assert result.rejected_overlap_count == 0
    assert result.rejected_budget_count == 0


def test_select_rejects_lower_priority_on_physical_overlap() -> None:
    high = succeeded_probe_at((3, 4), rank=1, equivalence_key="eq_high")
    low = succeeded_probe_at((3, 4), rank=9, equivalence_key="eq_low", gene_key="miner_seed_m1e_01")
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    selected, rejected = select_non_overlapping_candidates(
        normal_candidates=(low, high),
        budget_ctx=ctx,
    )
    assert [e.candidate.candidate_id for e in selected] == [high.candidate.candidate_id]
    assert len(rejected) == 1
    assert rejected[0].reason is RimPlacementRejectReason.PHYSICAL_OVERLAP
    assert rejected[0].reason.value == "PHYSICAL_OVERLAP"
    assert rejected[0].conflicting_candidate_id == high.candidate.candidate_id


def test_select_does_not_dedupe_equivalence_when_cells_disjoint() -> None:
    a = succeeded_probe_at((3, 4), rank=1, equivalence_key="same_eq")
    b = succeeded_probe_at(
        (10, 4),
        rank=2,
        equivalence_key="same_eq",
        mining=frozenset({(10, 4)}),
        transport=frozenset({(11, 4)}),
    )
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    selected, rejected = select_non_overlapping_candidates(
        normal_candidates=(a, b),
        budget_ctx=ctx,
    )
    assert len(selected) == 2
    assert rejected == ()


def test_build_placement_provisional_state_only() -> None:
    entry = succeeded_probe_at((3, 4))
    placement = build_rim_bundle_placement(entry)
    assert placement.placement_state is PlacementCommitState.PROVISIONAL_PLACED
    assert placement.occupied_cells == (
        entry.candidate.mining_occupied_cells | entry.candidate.transport_stub_cells
    )


def test_build_layer04_replay_frames_emits_begin_selected_complete() -> None:
    entry = succeeded_probe_at((3, 4))
    placement = build_rim_bundle_placement(entry)
    frames = build_layer04_replay_frames(selected=(placement,), rejected=())
    types = [f.frame_payload["event_type"] for f in frames]
    assert types[0] == EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN
    assert EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED in types
    assert types[-1] == EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE
    assert all(is_registered_event_type(t) for t in types)
    assert frames[1].frame_payload["placement_state"] == "PROVISIONAL_PLACED"


def _candidate_set_with(*entries: object) -> object:
    normal = entries
    return build_rim_bundle_candidate_set(
        normal_candidates=normal,  # type: ignore[arg-type]
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics(
            rim_anchor_count=1,
            seed_projection_attempt_count=0,
            local_geometry_rejected_count=0,
            route_probe_attempt_count=len(normal),
            route_probe_succeeded_count=len(normal),
            route_probe_failed_count=0,
            dedupe_duplicate_count=0,
            normal_candidate_count=len(normal),
            diagnostic_rejected_count=0,
            budget_skipped_count=0,
            layer_skip_reason=Layer03ExpansionMetrics.empty().layer_skip_reason,
        ),
    )


def test_run_layer04_does_not_mutate_complete_map() -> None:
    complete = golden_5x5_complete_map()
    cells_before = complete.cells
    candidate_set = _candidate_set_with(succeeded_probe_at((6, 4)))
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    result = run_layer_04_rim_bundle_placement(
        complete_map=complete,
        exterior_plan=minimal_l2_plan_for_golden(),
        candidate_set=candidate_set,
        budget_ctx=ctx,
    )
    assert complete.cells == cells_before
    assert result.selected_count == 1
    assert result.provisional_overlay.occupied_cells
    assert result.provisional_overlay.source_layer == "layer_04_rim_bundle_placement"


def test_layer04_never_outputs_routed_confirmed() -> None:
    candidate_set = _candidate_set_with(succeeded_probe_at((6, 4)))
    result = run_layer_04_rim_bundle_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        candidate_set=candidate_set,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert all(
        p.placement_state is PlacementCommitState.PROVISIONAL_PLACED
        for p in result.selected_placements
    )
    assert PlacementCommitState.ROUTED_CONFIRMED not in {
        p.placement_state for p in result.selected_placements
    }


def test_run_layer04_hold_when_exterior_plan_none() -> None:
    candidate_set = build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics.empty(),
    )
    result = run_layer_04_rim_bundle_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=None,
        candidate_set=candidate_set,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert result.selected_count == 0
    assert result.provisional_overlay.occupied_cells == frozenset()


def test_run_layer04_empty_normal_candidates_yields_empty_selection() -> None:
    candidate_set = build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics.empty(),
    )
    result = run_layer_04_rim_bundle_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        candidate_set=candidate_set,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert result.selected_count == 0
