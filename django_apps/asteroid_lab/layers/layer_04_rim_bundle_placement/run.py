"""Layer 4 — disabled shim (superseded by layer_03_rim_greedy_placement)."""

from __future__ import annotations

import warnings

from django_apps.asteroid_lab.layers.contracts.candidates import RimBundleCandidateSet
from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.layer04_disabled import Layer04DisabledResult
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
    complete_map: ReconstructionCompleteMap | None = None,
    exterior_plan: ExteriorConnectionPlan | None = None,
    candidate_set: RimBundleCandidateSet | None = None,
    budget_ctx: LayerBudgetContext | None = None,
) -> Layer04DisabledResult:
    _ = (complete_map, exterior_plan, candidate_set, budget_ctx)
    warnings.warn(
        "layer_04_rim_bundle_placement is disabled; use layer_03_rim_greedy_placement",
        DeprecationWarning,
        stacklevel=2,
    )
    return Layer04DisabledResult.superseded()


__all__ = ["empty_layer04_rim_placement_result", "run_layer_04_rim_bundle_placement"]
