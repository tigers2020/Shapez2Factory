"""L4-1 deterministic greedy inner fill."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    PATTERN_BUILTIN_1X1_FIELD_BLOCK,
    InnerPlacement,
    Layer04FillMetrics,
    Layer04InnerFillResult,
    Layer04SkipReason,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill import (
    candidate_domain,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def _coverage_ratio(occupied_count: int, candidate_count: int) -> float:
    if candidate_count == 0:
        return 0.0
    return occupied_count / candidate_count


def run_greedy_inner_fill(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    provisional_overlay: ProvisionalLayoutOverlay,
    budget_ctx: LayerBudgetContext,
) -> Layer04InnerFillResult:
    _ = exterior_plan
    candidates = candidate_domain.compute_interior_candidates(
        complete_map=complete_map,
        provisional_overlay=provisional_overlay,
    )
    ordered = candidate_domain.sorted_interior_candidates(candidates)
    if not ordered:
        return Layer04InnerFillResult(
            interior_occupied_cells=frozenset(),
            placements=(),
            metrics=Layer04FillMetrics(
                interior_occupied_cell_count=0,
                coverage_ratio=0.0,
                budget_interrupted=False,
            ),
            skip_reason=Layer04SkipReason.NO_CANDIDATES,
            corridor_shadow_cells=frozenset(),
        )

    placements: list[InnerPlacement] = []
    budget_interrupted = False
    for coord in ordered:
        if budget_ctx.remaining_budget_ms() <= 0:
            budget_interrupted = True
            break
        placements.append(
            InnerPlacement(
                coord=coord,
                pattern_id=PATTERN_BUILTIN_1X1_FIELD_BLOCK,
                rotation=0,
            )
        )

    occupied = frozenset(p.coord for p in placements)
    if not occupied and (budget_interrupted or budget_ctx.remaining_budget_ms() <= 0):
        return Layer04InnerFillResult(
            interior_occupied_cells=frozenset(),
            placements=(),
            metrics=Layer04FillMetrics(
                interior_occupied_cell_count=0,
                coverage_ratio=0.0,
                budget_interrupted=True,
            ),
            skip_reason=Layer04SkipReason.BUDGET_EXHAUSTED,
            corridor_shadow_cells=frozenset(),
        )

    return Layer04InnerFillResult(
        interior_occupied_cells=occupied,
        placements=tuple(placements),
        metrics=Layer04FillMetrics(
            interior_occupied_cell_count=len(occupied),
            coverage_ratio=_coverage_ratio(len(occupied), len(candidates)),
            budget_interrupted=budget_interrupted,
        ),
        skip_reason=None,
        corridor_shadow_cells=frozenset(),
    )


__all__ = ["run_greedy_inner_fill"]
