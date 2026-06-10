"""L4-1 deterministic greedy inner fill."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import BundleCellRole
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    PATTERN_BUILTIN_1X1_FIELD_BLOCK,
    InnerPlacement,
    Layer04FillMetrics,
    Layer04InnerFillResult,
    Layer04SkipReason,
    target_routeable_group_count_for_field,
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
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.inner_routeable_group import (  # noqa: E501
    place_routeable_inner_groups,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def _coverage_ratio(occupied_count: int, candidate_count: int) -> float:
    if candidate_count == 0:
        return 0.0
    return occupied_count / candidate_count


def _rim_group_count(provisional_overlay: ProvisionalLayoutOverlay) -> int:
    return len(
        {
            cell.placement_id
            for cell in provisional_overlay.by_cell.values()
            if cell.role is BundleCellRole.MINER
        }
    )


def run_greedy_inner_fill(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    provisional_overlay: ProvisionalLayoutOverlay,
    budget_ctx: LayerBudgetContext,
    target_routeable_group_count: int | None = None,
) -> Layer04InnerFillResult:
    connector_void_coords: frozenset[Coord] = frozenset()
    if exterior_plan is not None:
        connector_void_coords = frozenset(
            connector.void_coord
            for connector in exterior_plan.planned_connectors
            if connector.role is ExteriorConnectorRole.REQUIRED
        )
    initial_candidates = candidate_domain.compute_interior_candidates(
        complete_map=complete_map,
        provisional_overlay=provisional_overlay,
    )
    rim_count = _rim_group_count(provisional_overlay)
    routeable_target = (
        target_routeable_group_count
        if target_routeable_group_count is not None
        else target_routeable_group_count_for_field(len(complete_map.field_cells))
    )
    max_inner_routeable = max(0, routeable_target - rim_count)
    blocked = provisional_overlay.extractor_cells | provisional_overlay.extension_cells
    routeable_inner_groups = place_routeable_inner_groups(
        complete_map=complete_map,
        interior_candidates=initial_candidates,
        blocked_cells=blocked,
        connector_void_coords=connector_void_coords,
        max_groups=max_inner_routeable,
    )
    routeable_footprint: frozenset[Coord] = frozenset()
    for group in routeable_inner_groups:
        routeable_footprint |= group.miner_cells | group.extension_cells

    candidates = initial_candidates - routeable_footprint
    ordered = candidate_domain.sorted_interior_candidates(candidates)
    if not ordered and not routeable_inner_groups:
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

    occupied = frozenset(p.coord for p in placements) | routeable_footprint
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
        routeable_inner_groups=routeable_inner_groups,
        metrics=Layer04FillMetrics(
            interior_occupied_cell_count=len(occupied),
            coverage_ratio=_coverage_ratio(len(occupied), len(initial_candidates)),
            budget_interrupted=budget_interrupted,
        ),
        skip_reason=None,
        corridor_shadow_cells=frozenset(),
    )


__all__ = ["run_greedy_inner_fill"]
