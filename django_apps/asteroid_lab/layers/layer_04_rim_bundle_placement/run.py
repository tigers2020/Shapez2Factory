"""Layer 4 stub — rim bundle provisional placement (rebuild from skeleton)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import RimBundleCandidateSet
from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.provisional_overlay import ProvisionalLayoutOverlay
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    Layer04RimPlacementResult,
    build_layer04_rim_placement_result,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap


def empty_layer04_rim_placement_result() -> Layer04RimPlacementResult:
    return build_layer04_rim_placement_result(
        selected_placements=(),
        rejected_candidates=(),
        provisional_overlay=ProvisionalLayoutOverlay.empty(),
        replay_frames=(),
    )


def run_layer_04_rim_bundle_placement(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    candidate_set: RimBundleCandidateSet,
    budget_ctx: LayerBudgetContext,
) -> Layer04RimPlacementResult:
    _ = (complete_map, exterior_plan, candidate_set, budget_ctx)
    return empty_layer04_rim_placement_result()


__all__ = ["empty_layer04_rim_placement_result", "run_layer_04_rim_bundle_placement"]
