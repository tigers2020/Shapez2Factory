"""Layer 4 inner pattern fill skeleton — algorithm reset."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.inner_fill_strategy import (
    InnerFillStrategy,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    Layer04InnerFillResult,
    Layer04SkipReason,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
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
    target_routeable_group_count: int | None = None,
    inner_fill_strategy: InnerFillStrategy | str = InnerFillStrategy.GREEDY,
) -> Layer04InnerFillResult:
    _ = (
        complete_map,
        exterior_plan,
        provisional_overlay,
        budget_ctx,
        target_routeable_group_count,
        inner_fill_strategy,
    )
    empty = Layer04InnerFillResult.empty()
    return Layer04InnerFillResult(
        interior_occupied_cells=empty.interior_occupied_cells,
        placements=empty.placements,
        routeable_inner_groups=empty.routeable_inner_groups,
        metrics=empty.metrics,
        skip_reason=Layer04SkipReason.MACRO_ONLY_DEFERRED,
        corridor_shadow_cells=empty.corridor_shadow_cells,
        trunk_diagnostics=empty.trunk_diagnostics,
    )


run_layer_05_inner_pattern_fill = run_layer_04_inner_pattern_fill

__all__ = ["run_layer_04_inner_pattern_fill", "run_layer_05_inner_pattern_fill"]
