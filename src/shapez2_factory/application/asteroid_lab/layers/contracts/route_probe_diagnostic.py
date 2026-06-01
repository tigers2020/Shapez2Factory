"""Structured diagnostics for Layer 03 route probe failures (PR-C audit)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    CandidateRejectReason,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import RouteGoal
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    TransportKind,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord, neighbors4


@dataclass(frozen=True, slots=True)
class RouteProbeDiagnostic:
    anchor_coord: Coord
    stub_coord: Coord
    output_dir: str
    transport_kind: TransportKind
    bfs_limit: int
    visited_count: int
    max_depth_reached: int
    frontier_exhausted: bool
    probe_limit_hit: bool
    nearest_goal_manhattan: int | None
    reachable_goal_count: int
    same_void_component_goal_count: int
    stub_component_id: str | None
    goal_component_ids: tuple[str, ...]
    detailed_unreachable_reason: str


def label_void_components(external_void_cells: frozenset[Coord]) -> dict[Coord, str]:
    """Deterministic void-island labels (4-neighbor on external void only)."""

    remaining = set(external_void_cells)
    labels: dict[Coord, str] = {}
    comp_index = 0
    for seed in sorted(external_void_cells):
        if seed not in remaining:
            continue
        queue: deque[Coord] = deque([seed])
        component_cells: list[Coord] = []
        while queue:
            current = queue.popleft()
            if current not in remaining:
                continue
            remaining.remove(current)
            component_cells.append(current)
            for neighbor in neighbors4(current):
                if neighbor in remaining:
                    queue.append(neighbor)
        component_cells.sort()
        component_id = f"void_{component_cells[0][0]}_{component_cells[0][1]}_{comp_index}"
        comp_index += 1
        for cell in component_cells:
            labels[cell] = component_id
    return labels


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _stub_void_coord(
    *,
    stub_cells: frozenset[Coord],
    probe_start: Coord,
    external_void_cells: frozenset[Coord],
) -> Coord | None:
    for cell in sorted(stub_cells):
        if cell in external_void_cells:
            return cell
    if probe_start in external_void_cells:
        return probe_start
    return None


def _unweighted_walkable_bfs(
    *,
    start: Coord,
    walkable_cells: frozenset[Coord],
    goal_coords: frozenset[Coord],
    step_limit: int | None = None,
) -> tuple[dict[Coord, int], int, bool]:
    """Return distances, visited count, and whether search stopped due to step_limit."""

    distances: dict[Coord, int] = {start: 0}
    queue: deque[Coord] = deque([start])
    limit_hit = False
    while queue:
        current = queue.popleft()
        depth = distances[current]
        if step_limit is not None and depth >= step_limit:
            limit_hit = True
            continue
        for neighbor in neighbors4(current):
            if neighbor not in walkable_cells or neighbor in distances:
                continue
            distances[neighbor] = depth + 1
            queue.append(neighbor)
    return distances, len(distances), limit_hit


def classify_exterior_goal_unreachable(
    *,
    anchor_coord: Coord,
    stub_coord: Coord,
    output_dir: str,
    transport_kind: TransportKind,
    probe_start: Coord,
    stub_cells: frozenset[Coord],
    matching_goals: tuple[RouteGoal, ...],
    walkable_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord],
    bfs_limit: int,
    visited_count: int,
    max_depth_reached: int,
    frontier_exhausted: bool,
    probe_limit_hit: bool,
) -> tuple[CandidateRejectReason, RouteProbeDiagnostic]:
    """Map a failed probe to a detailed reject reason + diagnostic payload."""

    void_labels = label_void_components(external_void_cells)
    stub_void = _stub_void_coord(
        stub_cells=stub_cells,
        probe_start=probe_start,
        external_void_cells=external_void_cells,
    )
    stub_component_id = void_labels.get(stub_void) if stub_void is not None else None
    goal_component_ids = tuple(
        sorted(
            {
                void_labels[goal.coord]
                for goal in matching_goals
                if goal.coord in void_labels
            }
        )
    )
    same_component_goals = [
        goal
        for goal in matching_goals
        if stub_component_id is not None and void_labels.get(goal.coord) == stub_component_id
    ]
    nearest_manhattan = (
        min(_manhattan(probe_start, goal.coord) for goal in matching_goals)
        if matching_goals
        else None
    )

    if not matching_goals:
        reason = CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_NO_GOALS
    elif probe_start not in walkable_cells:
        reason = CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_INVALID_STUB_COMPONENT
    elif matching_goals and not same_component_goals:
        reason = CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_NO_SAME_VOID_COMPONENT
    else:
        goal_coords = frozenset(goal.coord for goal in matching_goals)
        distances, _, _ = _unweighted_walkable_bfs(
            start=probe_start,
            walkable_cells=walkable_cells,
            goal_coords=goal_coords,
        )
        reachable = [goal for goal in matching_goals if goal.coord in distances]
        if reachable:
            shortest = min(distances[goal.coord] for goal in reachable)
            if shortest > bfs_limit or probe_limit_hit:
                reason = CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_PROBE_LIMIT_HIT
            else:
                reason = CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_FRONTIER_EXHAUSTED
        elif probe_limit_hit:
            reason = CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_PROBE_LIMIT_HIT
        else:
            reason = CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_FRONTIER_EXHAUSTED

    if reason is CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_PROBE_LIMIT_HIT:
        probe_limit_hit = True

    diagnostic = RouteProbeDiagnostic(
        anchor_coord=anchor_coord,
        stub_coord=stub_coord,
        output_dir=output_dir,
        transport_kind=transport_kind,
        bfs_limit=bfs_limit,
        visited_count=visited_count,
        max_depth_reached=max_depth_reached,
        frontier_exhausted=frontier_exhausted,
        probe_limit_hit=probe_limit_hit,
        nearest_goal_manhattan=nearest_manhattan,
        reachable_goal_count=len(
            [goal for goal in matching_goals if goal.coord in walkable_cells]
        ),
        same_void_component_goal_count=len(same_component_goals),
        stub_component_id=stub_component_id,
        goal_component_ids=goal_component_ids,
        detailed_unreachable_reason=reason.value,
    )
    return reason, diagnostic


__all__ = [
    "RouteProbeDiagnostic",
    "classify_exterior_goal_unreachable",
    "label_void_components",
]
