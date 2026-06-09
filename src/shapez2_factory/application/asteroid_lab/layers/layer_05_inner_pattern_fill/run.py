"""Layer 5 package path; canonical entry is ``run_layer_04_inner_pattern_fill`` (PR-1 renumber)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    Layer04InnerFillResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.greedy import (
    run_greedy_inner_fill,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def run_layer_04_inner_pattern_fill(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    provisional_overlay: ProvisionalLayoutOverlay,
    budget_ctx: LayerBudgetContext,
) -> Layer04InnerFillResult:
    return run_greedy_inner_fill(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        provisional_overlay=provisional_overlay,
        budget_ctx=budget_ctx,
    )


run_layer_05_inner_pattern_fill = run_layer_04_inner_pattern_fill

__all__ = ["run_layer_04_inner_pattern_fill", "run_layer_05_inner_pattern_fill"]
