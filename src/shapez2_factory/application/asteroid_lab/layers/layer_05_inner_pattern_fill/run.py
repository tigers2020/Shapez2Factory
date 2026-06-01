"""Layer 5 stub ??inner pattern fill (PR-3c signature only)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_placement import (
    Layer04RimPlacementResult,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def run_layer_05_inner_pattern_fill(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    rim_placement_result: Layer04RimPlacementResult,
    provisional_overlay: ProvisionalLayoutOverlay,
    budget_ctx: LayerBudgetContext,
) -> None:
    _ = (
        complete_map,
        exterior_plan,
        rim_placement_result,
        provisional_overlay,
        budget_ctx,
    )


__all__ = ["run_layer_05_inner_pattern_fill"]
