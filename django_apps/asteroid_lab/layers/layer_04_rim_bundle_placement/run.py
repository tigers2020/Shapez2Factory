"""Layer 4 — rim bundle provisional placement + overlay materialization."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import RimBundleCandidateSet
from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.provisional_overlay import ProvisionalLayoutOverlay
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    Layer04RimPlacementResult,
    build_layer04_rim_placement_result,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.place import (
    build_provisional_overlay,
    build_rim_bundle_placement,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select import (
    select_non_overlapping_candidates,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap


def empty_layer04_rim_placement_result() -> Layer04RimPlacementResult:
    overlay = ProvisionalLayoutOverlay.empty()
    return build_layer04_rim_placement_result(
        selected_placements=(),
        rejected_candidates=(),
        provisional_overlay=overlay,
        replay_frames=(),
    )


def run_layer_04_rim_bundle_placement(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    candidate_set: RimBundleCandidateSet,
    budget_ctx: LayerBudgetContext,
) -> Layer04RimPlacementResult:
    _ = complete_map
    if exterior_plan is None or not candidate_set.normal_candidates:
        return empty_layer04_rim_placement_result()

    selected_entries, rejected = select_non_overlapping_candidates(
        normal_candidates=candidate_set.normal_candidates,
        budget_ctx=budget_ctx,
    )
    placements = tuple(build_rim_bundle_placement(entry) for entry in selected_entries)
    overlay = build_provisional_overlay(placements)
    return build_layer04_rim_placement_result(
        selected_placements=placements,
        rejected_candidates=rejected,
        provisional_overlay=overlay,
        replay_frames=(),
    )


__all__ = ["empty_layer04_rim_placement_result", "run_layer_04_rim_bundle_placement"]
