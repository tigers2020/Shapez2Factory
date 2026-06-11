"""Trunk-first weighted rip-up inner fill (L5 package, L4 slug).

Belt/trunk path to exterior is committed before miners. Miners/extensions attach
only when output connects to the committed belt network. Provisional placements
may be ripped up by lowest removal weight (extension=1.0, miner=1.5×).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

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
    RouteableInnerGroupPlacement,
    target_routeable_group_count_for_field,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.trunk_first_inner_fill_diagnostics import (  # noqa: E501
    TrunkFirstInnerFillDiagnostics,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.space_lift_routing import (  # noqa: E501
    connector_reachable_void_cells,
    lift_void_egress_for_stub,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill import (
    candidate_domain,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.inner_routeable_group import (  # noqa: E501
    _INNER_MINER_THROUGHPUT_FACTOR,
    _M3E_EAST_FIELD_OFFSETS,
    _M3E_EAST_STUB_OFFSET,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord, neighbors4
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

EXTENSION_BASE_WEIGHT = 1.0
MINER_WEIGHT_MULTIPLIER = 1.5
MAX_EXTENSIONS_PER_MINER = 3
MAX_RIPUP_ATTEMPTS_PER_ITERATION = 32
MAX_SOLVER_ITERATIONS = 256


@dataclass
class _RipupStats:
    ripup_event_count: int = 0
    removed_miner_count: int = 0
    removed_extension_count: int = 0
    orphan_extension_pruned_count: int = 0
    failed_belt_route_count: int = 0
    failed_miner_attach_count: int = 0


@dataclass
class _SolverState:
    complete_map: ReconstructionCompleteMap
    fixed_blocked: frozenset[Coord]
    connector_void_coords: frozenset[Coord]
    committed_belt_cells: set[Coord] = field(default_factory=set)
    confirmed_groups: list[RouteableInnerGroupPlacement] = field(default_factory=list)
    provisional_groups: list[RouteableInnerGroupPlacement] = field(default_factory=list)
    field_blocks: list[InnerPlacement] = field(default_factory=list)
    stats: _RipupStats = field(default_factory=_RipupStats)

    def all_occupied(self) -> frozenset[Coord]:
        cells: set[Coord] = set(self.fixed_blocked)
        cells |= self.committed_belt_cells
        for group in self.confirmed_groups + self.provisional_groups:
            cells |= group.miner_cells | group.extension_cells | {group.m_output_stub}
        cells |= {p.coord for p in self.field_blocks}
        return frozenset(cells)

    def removal_weight(self, group: RouteableInnerGroupPlacement) -> float:
        ext_count = min(len(group.extension_cells), MAX_EXTENSIONS_PER_MINER)
        return (ext_count * EXTENSION_BASE_WEIGHT) + (
            MINER_WEIGHT_MULTIPLIER * EXTENSION_BASE_WEIGHT
        )


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _footprint_at_anchor(anchor: Coord) -> tuple[frozenset[Coord], frozenset[Coord], Coord]:
    ax, ay = anchor
    field_cells = frozenset((ax + dx, ay + dy) for dx, dy in _M3E_EAST_FIELD_OFFSETS)
    miner_cells = frozenset({anchor})
    extension_cells = frozenset(list(field_cells - miner_cells)[:MAX_EXTENSIONS_PER_MINER])
    stub = (ax + _M3E_EAST_STUB_OFFSET[0], ay + _M3E_EAST_STUB_OFFSET[1])
    return miner_cells, extension_cells, stub


def _trunk_goal_cells(
    *,
    complete_map: ReconstructionCompleteMap,
    connector_void_coords: frozenset[Coord],
) -> frozenset[Coord]:
    if not connector_void_coords:
        return frozenset()
    reachable_void = connector_reachable_void_cells(
        complete_map=complete_map,
        connector_void_coords=connector_void_coords,
    )
    goals: set[Coord] = set()
    for void_coord in reachable_void:
        for neighbor in neighbors4(void_coord):
            if neighbor in complete_map.field_cells:
                goals.add(neighbor)
    return frozenset(goals)


def _belt_walkable_cells(state: _SolverState) -> frozenset[Coord]:
    occupied = state.all_occupied()
    belt = state.committed_belt_cells
    return frozenset(
        c for c in state.complete_map.field_cells if c in belt or c not in occupied
    )


def _bfs_trunk_path(
    *,
    state: _SolverState,
    start: Coord,
    goals: frozenset[Coord],
) -> tuple[Coord, ...] | None:
    if start in goals:
        return (start,)
    walkable = _belt_walkable_cells(state)
    if start not in walkable:
        return None
    queue: deque[Coord] = deque([start])
    parents: dict[Coord, Coord | None] = {start: None}
    while queue:
        current = queue.popleft()
        if current in goals:
            path: list[Coord] = []
            node: Coord | None = current
            while node is not None:
                path.append(node)
                node = parents[node]
            path.reverse()
            return tuple(path)
        for nxt in sorted(neighbors4(current), key=lambda c: (c[0], c[1])):
            if nxt in parents or nxt not in walkable:
                continue
            parents[nxt] = current
            queue.append(nxt)
    return None


def _pick_interior_belt_seed(
    *,
    interior_candidates: frozenset[Coord],
    goals: frozenset[Coord],
) -> Coord | None:
    if not interior_candidates or not goals:
        return None
    ranked = sorted(
        interior_candidates,
        key=lambda c: (min(_manhattan(c, g) for g in goals), c[0], c[1]),
    )
    return ranked[0]


def _commit_belt_path(state: _SolverState, path: tuple[Coord, ...]) -> None:
    for cell in path:
        state.committed_belt_cells.add(cell)


def _stub_connected_to_trunk(
    *,
    state: _SolverState,
    stub: Coord,
) -> bool:
    if stub in state.committed_belt_cells:
        return True
    for neighbor in neighbors4(stub):
        if neighbor in state.committed_belt_cells:
            return True
    return False


def _miner_confirmed(
    *,
    state: _SolverState,
    group: RouteableInnerGroupPlacement,
) -> bool:
    if not _stub_connected_to_trunk(state=state, stub=group.m_output_stub):
        return False
    if not lift_void_egress_for_stub(
        stub=group.m_output_stub,
        complete_map=state.complete_map,
        connector_void_coords=state.connector_void_coords,
    ):
        return False
    return True


def _try_attach_miner_on_belt(
    *,
    state: _SolverState,
    interior_candidates: frozenset[Coord],
    placement_index: int,
) -> RouteableInnerGroupPlacement | None:
    belt_cells = sorted(state.committed_belt_cells, key=lambda c: (c[0], c[1]))
    occupied = state.all_occupied()
    for belt_cell in belt_cells:
        for neighbor in sorted(neighbors4(belt_cell), key=lambda c: (c[0], c[1])):
            if neighbor not in interior_candidates:
                continue
            anchor = neighbor
            miner_cells, extension_cells, stub = _footprint_at_anchor(anchor)
            if stub != belt_cell:
                continue
            footprint = miner_cells | extension_cells | {stub}
            if not footprint <= state.complete_map.field_cells:
                continue
            overlap = footprint & occupied
            overlap -= state.committed_belt_cells
            if overlap:
                continue
            if not _stub_connected_to_trunk(state=state, stub=stub):
                continue
            return RouteableInnerGroupPlacement(
                placement_id=f"l4-inner-{placement_index:04d}",
                anchor=anchor,
                miner_cells=miner_cells,
                extension_cells=extension_cells,
                m_output_stub=stub,
                throughput_factor=_INNER_MINER_THROUGHPUT_FACTOR,
            )
    return None


def _prune_orphan_extensions(state: _SolverState) -> None:
    confirmed_ids = {g.placement_id for g in state.confirmed_groups}
    pruned: list[RouteableInnerGroupPlacement] = []
    for group in state.provisional_groups:
        if group.placement_id not in confirmed_ids:
            state.stats.orphan_extension_pruned_count += len(group.extension_cells)
            state.stats.removed_extension_count += len(group.extension_cells)
            state.stats.removed_miner_count += 1
            continue
        pruned.append(group)
    state.provisional_groups = pruned


def _rip_up_lowest_weight_blocker(state: _SolverState) -> bool:
    if not state.provisional_groups:
        return False
    ranked = sorted(
        state.provisional_groups,
        key=lambda g: (state.removal_weight(g), g.placement_id),
    )
    victim = ranked[0]
    state.provisional_groups = [g for g in state.provisional_groups if g is not victim]
    state.stats.ripup_event_count += 1
    state.stats.removed_miner_count += 1
    state.stats.removed_extension_count += len(victim.extension_cells)
    return True


def _confirm_eligible_groups(state: _SolverState) -> None:
    still_provisional: list[RouteableInnerGroupPlacement] = []
    for group in state.provisional_groups:
        if _miner_confirmed(state=state, group=group):
            state.confirmed_groups.append(group)
        else:
            still_provisional.append(group)
    state.provisional_groups = still_provisional


def _rim_group_count(provisional_overlay: ProvisionalLayoutOverlay) -> int:
    from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
        BundleCellRole,
    )

    return len(
        {
            cell.placement_id
            for cell in provisional_overlay.by_cell.values()
            if cell.role is BundleCellRole.MINER
        }
    )


def _coverage_ratio(occupied_count: int, candidate_count: int) -> float:
    if candidate_count == 0:
        return 0.0
    return occupied_count / candidate_count


def run_trunk_first_weighted_ripup_inner_fill(
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

    fixed_blocked = (
        provisional_overlay.extractor_cells
        | provisional_overlay.extension_cells
        | provisional_overlay.transport_stub_cells
    )

    state = _SolverState(
        complete_map=complete_map,
        fixed_blocked=fixed_blocked,
        connector_void_coords=connector_void_coords,
    )

    goals = _trunk_goal_cells(
        complete_map=complete_map,
        connector_void_coords=connector_void_coords,
    )
    budget_interrupted = False
    iterations = 0
    trunk_path_count = 0

    while (
        len(state.confirmed_groups) < max_inner_routeable
        and iterations < MAX_SOLVER_ITERATIONS
        and budget_ctx.remaining_budget_ms() > 0
    ):
        iterations += 1
        occupied = state.all_occupied()
        interior_candidates = initial_candidates - occupied
        seed = _pick_interior_belt_seed(
            interior_candidates=interior_candidates,
            goals=goals,
        )
        if seed is None or not goals:
            state.stats.failed_belt_route_count += 1
            if not _rip_up_lowest_weight_blocker(state):
                break
            _prune_orphan_extensions(state)
            continue

        path = _bfs_trunk_path(state=state, start=seed, goals=goals)
        rip_attempts = 0
        while path is None and rip_attempts < MAX_RIPUP_ATTEMPTS_PER_ITERATION:
            rip_attempts += 1
            state.stats.failed_belt_route_count += 1
            if not _rip_up_lowest_weight_blocker(state):
                break
            _prune_orphan_extensions(state)
            path = _bfs_trunk_path(state=state, start=seed, goals=goals)
        if path is None:
            break

        _commit_belt_path(state, path)
        trunk_path_count += 1

        placement_index = len(state.confirmed_groups) + len(state.provisional_groups) + 1
        group = _try_attach_miner_on_belt(
            state=state,
            interior_candidates=interior_candidates,
            placement_index=placement_index,
        )
        if group is None:
            state.stats.failed_miner_attach_count += 1
            continue
        state.provisional_groups.append(group)
        _confirm_eligible_groups(state)
        _prune_orphan_extensions(state)

        if budget_ctx.remaining_budget_ms() <= 0:
            budget_interrupted = True
            break

    _confirm_eligible_groups(state)
    _prune_orphan_extensions(state)

    routeable_footprint: frozenset[Coord] = frozenset()
    for group in state.confirmed_groups:
        routeable_footprint |= group.miner_cells | group.extension_cells

    remaining_candidates = initial_candidates - state.all_occupied()
    for coord in candidate_domain.sorted_interior_candidates(remaining_candidates):
        if budget_ctx.remaining_budget_ms() <= 0:
            budget_interrupted = True
            break
        state.field_blocks.append(
            InnerPlacement(
                coord=coord,
                pattern_id=PATTERN_BUILTIN_1X1_FIELD_BLOCK,
                rotation=0,
            )
        )

    occupied = routeable_footprint | {p.coord for p in state.field_blocks}
    if not occupied and budget_interrupted:
        return Layer04InnerFillResult(
            interior_occupied_cells=frozenset(),
            placements=(),
            metrics=Layer04FillMetrics(
                interior_occupied_cell_count=0,
                coverage_ratio=0.0,
                budget_interrupted=True,
            ),
            skip_reason=Layer04SkipReason.BUDGET_EXHAUSTED,
            corridor_shadow_cells=frozenset(state.committed_belt_cells),
            trunk_diagnostics=TrunkFirstInnerFillDiagnostics(
                trunk_path_count=trunk_path_count,
                failed_belt_route_count=state.stats.failed_belt_route_count,
                failed_miner_attach_count=state.stats.failed_miner_attach_count,
                ripup_event_count=state.stats.ripup_event_count,
                removed_miner_count=state.stats.removed_miner_count,
                removed_extension_count=state.stats.removed_extension_count,
                orphan_extension_pruned_count=state.stats.orphan_extension_pruned_count,
                final_connected_miner_count=len(state.confirmed_groups),
                trunk_connected_miner_count=len(state.confirmed_groups),
                final_orphan_extension_count=0,
            ),
        )

    if not occupied and not initial_candidates:
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

    diagnostics = TrunkFirstInnerFillDiagnostics(
        trunk_path_count=trunk_path_count,
        trunk_connected_miner_count=len(state.confirmed_groups),
        ripup_event_count=state.stats.ripup_event_count,
        removed_miner_count=state.stats.removed_miner_count,
        removed_extension_count=state.stats.removed_extension_count,
        orphan_extension_pruned_count=state.stats.orphan_extension_pruned_count,
        failed_belt_route_count=state.stats.failed_belt_route_count,
        failed_miner_attach_count=state.stats.failed_miner_attach_count,
        final_connected_miner_count=len(state.confirmed_groups),
        final_orphan_extension_count=sum(
            len(g.extension_cells)
            for g in state.provisional_groups
            if g.placement_id not in {x.placement_id for x in state.confirmed_groups}
        ),
    )

    return Layer04InnerFillResult(
        interior_occupied_cells=occupied,
        placements=tuple(state.field_blocks),
        routeable_inner_groups=tuple(state.confirmed_groups),
        metrics=Layer04FillMetrics(
            interior_occupied_cell_count=len(occupied),
            coverage_ratio=_coverage_ratio(len(occupied), len(initial_candidates)),
            budget_interrupted=budget_interrupted,
        ),
        skip_reason=None,
        corridor_shadow_cells=frozenset(state.committed_belt_cells),
        trunk_diagnostics=diagnostics,
    )


__all__ = [
    "EXTENSION_BASE_WEIGHT",
    "MAX_EXTENSIONS_PER_MINER",
    "MINER_WEIGHT_MULTIPLIER",
    "run_trunk_first_weighted_ripup_inner_fill",
]
