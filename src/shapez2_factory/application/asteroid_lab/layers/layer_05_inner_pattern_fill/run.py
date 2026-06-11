"""Layer 5 package path; canonical entry is ``run_layer_04_inner_pattern_fill`` (PR-1 renumber)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.inner_fill_strategy import (
    InnerFillStrategy,
    parse_inner_fill_strategy,
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
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.trunk_first_weighted_ripup_solver import (  # noqa: E501
    run_trunk_first_weighted_ripup_inner_fill,
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
    strategy = parse_inner_fill_strategy(inner_fill_strategy)
    kwargs = {
        "complete_map": complete_map,
        "exterior_plan": exterior_plan,
        "provisional_overlay": provisional_overlay,
        "budget_ctx": budget_ctx,
        "target_routeable_group_count": target_routeable_group_count,
    }
    if strategy is InnerFillStrategy.TRUNK_FIRST_WEIGHTED_RIPUP:
        return run_trunk_first_weighted_ripup_inner_fill(**kwargs)
    return run_greedy_inner_fill(**kwargs)


run_layer_05_inner_pattern_fill = run_layer_04_inner_pattern_fill

__all__ = ["run_layer_04_inner_pattern_fill", "run_layer_05_inner_pattern_fill"]
