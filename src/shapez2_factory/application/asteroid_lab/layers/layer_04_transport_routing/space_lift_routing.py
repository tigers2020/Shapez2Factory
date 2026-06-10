"""Space Lift egress routing for L4 inner sources (z=0 field → z=1 void)."""

from __future__ import annotations

from collections import deque

from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04SourceView,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import RouteGoal
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.astar import (
    AstarPathResult,
    astar_to_nearest_goal,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.route_domain import (  # noqa: E501
    L4RouteSearchDomain,
    L4TerrainKind,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord, neighbors4
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

INNER_LIFT_SOURCE_PLACEMENT_PREFIX = "l4-inner-"
SPACE_LIFT_FIELD_Z = 0
SPACE_LIFT_VOID_Z = 1


def is_inner_lift_source(placement_id: str) -> bool:
    return placement_id.startswith(INNER_LIFT_SOURCE_PLACEMENT_PREFIX)


def connector_reachable_void_cells(
    *,
    complete_map: ReconstructionCompleteMap,
    connector_void_coords: frozenset[Coord],
) -> frozenset[Coord]:
    field_cells = complete_map.field_cells
    void_cells = complete_map.external_void_cells - field_cells
    if not connector_void_coords or not void_cells:
        return frozenset()
    seeds = frozenset(c for c in connector_void_coords if c in void_cells)
    if not seeds:
        return frozenset()
    seen = set(seeds)
    queue: deque[Coord] = deque(seeds)
    while queue:
        current = queue.popleft()
        for nxt in neighbors4(current):
            if nxt in seen or nxt not in void_cells:
                continue
            seen.add(nxt)
            queue.append(nxt)
    return frozenset(seen)


def lift_void_egress_for_stub(
    *,
    stub: Coord,
    complete_map: ReconstructionCompleteMap,
    connector_void_coords: frozenset[Coord],
) -> Coord | None:
    """Pick void cell on z=1 network for lift egress nearest to ``stub``."""

    reachable = connector_reachable_void_cells(
        complete_map=complete_map,
        connector_void_coords=connector_void_coords,
    )
    if not reachable:
        return None
    if stub in reachable:
        return stub
    best: Coord | None = None
    best_dist = 10**9
    for void_coord in reachable:
        dist = abs(stub[0] - void_coord[0]) + abs(stub[1] - void_coord[1])
        if dist < best_dist:
            best_dist = dist
            best = void_coord
    return best


def build_void_shell_route_domain(
    *,
    complete_map: ReconstructionCompleteMap,
    connector_void_coords: frozenset[Coord],
) -> L4RouteSearchDomain | None:
    reachable = connector_reachable_void_cells(
        complete_map=complete_map,
        connector_void_coords=connector_void_coords,
    )
    if not reachable:
        return None
    from shapez2_factory.domain.asteroid_lab.grid_contract import bbox_from_coords

    terrain_at: dict[Coord, L4TerrainKind] = {coord: "void" for coord in reachable}
    bbox = bbox_from_coords(reachable)
    return L4RouteSearchDomain(
        search_bbox=bbox,
        walkable_cells=reachable,
        terrain_at=terrain_at,
    )


def _coords_adjacent(left: Coord, right: Coord) -> bool:
    return abs(left[0] - right[0]) + abs(left[1] - right[1]) == 1


def _prepend_lift_segment(
    *,
    stub: Coord,
    void_path: tuple[Coord, ...],
    egress: Coord,
) -> tuple[Coord, ...]:
    """Void belt path; prepend field stub only when grid-adjacent to egress."""

    if not void_path:
        if stub == egress:
            return (stub,)
        if _coords_adjacent(stub, egress):
            return (stub, egress)
        return (egress,)
    if stub == egress or not _coords_adjacent(stub, egress):
        return void_path
    return (stub,) + void_path


def astar_inner_source_via_space_lift(
    *,
    source: Layer04SourceView,
    complete_map: ReconstructionCompleteMap,
    connector_void_coords: frozenset[Coord],
    goals: tuple[RouteGoal, ...],
) -> AstarPathResult | None:
    """Route inner source: lift from field stub to z=1 void, then void-only A*."""

    if not is_inner_lift_source(source.placement_id):
        return None
    egress = lift_void_egress_for_stub(
        stub=source.m_output_stub,
        complete_map=complete_map,
        connector_void_coords=connector_void_coords,
    )
    if egress is None:
        return None
    domain = build_void_shell_route_domain(
        complete_map=complete_map,
        connector_void_coords=connector_void_coords,
    )
    if domain is None:
        return None
    if domain.step_cost(egress) is None:
        return None
    result = astar_to_nearest_goal(domain=domain, start=egress, goals=goals)
    if result is None:
        return None
    path = _prepend_lift_segment(
        stub=source.m_output_stub,
        void_path=result.path,
        egress=egress,
    )
    lift_penalty = 5
    return AstarPathResult(
        path=path,
        route_cost=result.route_cost + lift_penalty,
        goal_coord=result.goal_coord,
        goal_id=result.goal_id,
    )


__all__ = [
    "INNER_LIFT_SOURCE_PLACEMENT_PREFIX",
    "SPACE_LIFT_FIELD_Z",
    "SPACE_LIFT_VOID_Z",
    "astar_inner_source_via_space_lift",
    "build_void_shell_route_domain",
    "connector_reachable_void_cells",
    "is_inner_lift_source",
    "lift_void_egress_for_stub",
]
