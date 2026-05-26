"""Lift column + trunk mask route domain for RTTP v0.1 (PR-2)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.snapshots.grid_contract import neighbors4


@dataclass(frozen=True, slots=True)
class LiftEdge:
    platform_coord: Coord
    lift_coord: Coord
    lane_id: int


@dataclass(frozen=True, slots=True)
class RouteCellDomain:
    """Aggregate probe domain: floor blocked except platform→lift; trunk walk on mask + goals."""

    blocked_cells: frozenset[Coord]
    trunk_mask_cells: frozenset[Coord]
    lift_edges: tuple[LiftEdge, ...]
    traversable_cells: frozenset[Coord]
    step_costs: frozenset[tuple[Coord, int]] = frozenset()


def build_route_domain_from_skeleton(
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
) -> RouteCellDomain:
    """Build v0.1 route domain from skeleton trunk mask and lift columns."""

    lift_edges = tuple(
        LiftEdge(
            platform_coord=column.platform_coord,
            lift_coord=column.lift_coord,
            lane_id=column.target_lane,
        )
        for column in skeleton.lift_columns
    )
    platform_cells = frozenset(edge.platform_coord for edge in lift_edges)
    lift_coords = frozenset(edge.lift_coord for edge in lift_edges)
    incompatible = inp.blocked_incompatible_transport_cells
    trunk_mask = frozenset(skeleton.trunk_mask_cells - incompatible)
    goal_coords = probe_goal_coords(inp, skeleton)

    void_walkable = frozenset(inp.external_void_cells - incompatible)
    blocked = frozenset(
        inp.mineable_cells - platform_cells - lift_coords - incompatible
    )
    traversable = frozenset(
        (trunk_mask | lift_coords | goal_coords | void_walkable) - incompatible
    )
    step_costs: dict[Coord, int] = {}
    for coord in void_walkable:
        step_costs[coord] = 1
    for coord in trunk_mask | lift_coords | goal_coords:
        step_costs.setdefault(coord, 2)

    return RouteCellDomain(
        blocked_cells=blocked,
        trunk_mask_cells=trunk_mask,
        lift_edges=lift_edges,
        traversable_cells=traversable,
        step_costs=frozenset(step_costs.items()),
    )


def path_exists_via_lift(
    domain: RouteCellDomain,
    start: Coord,
    goals: frozenset[Coord],
) -> bool:
    """BFS: platform stub → optional lift edge → trunk mask / goals walk."""

    if not goals:
        return False
    if start in goals:
        return True

    queue: deque[tuple[Coord, str]] = deque([(start, "platform")])
    visited: set[tuple[Coord, str]] = {(start, "platform")}

    while queue:
        coord, phase = queue.popleft()
        if phase == "trunk" and coord in goals:
            return True

        if phase == "platform":
            for edge in domain.lift_edges:
                if edge.platform_coord != coord:
                    continue
                next_state = (edge.lift_coord, "trunk")
                if next_state not in visited:
                    visited.add(next_state)
                    queue.append(next_state)
            continue

        for neighbor in neighbors4(coord):
            if neighbor in domain.blocked_cells:
                continue
            if neighbor not in domain.traversable_cells and neighbor not in goals:
                continue
            next_state = (neighbor, "trunk")
            if next_state in visited:
                continue
            visited.add(next_state)
            queue.append(next_state)

    return False


__all__ = [
    "LiftEdge",
    "RouteCellDomain",
    "build_route_domain_from_skeleton",
    "path_exists_via_lift",
]
