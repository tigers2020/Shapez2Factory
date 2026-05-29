"""Build bounded virtual exterior transport domain for L3 route probe."""

from __future__ import annotations

from collections import deque

from django_apps.asteroid_lab.layers.contracts.exterior_transport_domain import (
    ExteriorTransportDomain,
)
from django_apps.asteroid_lab.layers.contracts.route_goal import RouteGoal
from django_apps.asteroid_lab.layers.contracts.weighted_transport_route_domain import (
    WeightedTransportRouteDomain,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.grid_contract import (
    Coord,
    bbox_from_coords,
    cells_in_bbox,
    expand_bbox,
    neighbors4,
)

EXTERIOR_TRANSPORT_MARGIN_CELLS = 8


def build_exterior_transport_domain(
    *,
    complete_map: ReconstructionCompleteMap,
    anchor_abs: Coord,
    transport_stub_cells: frozenset[Coord],
    route_goals: tuple[RouteGoal, ...],
    route_probe_start: Coord,
) -> ExteriorTransportDomain:
    envelope = frozenset(
        {
            anchor_abs,
            route_probe_start,
            *transport_stub_cells,
            *(goal.coord for goal in route_goals),
        }
    )
    bb = expand_bbox(bbox_from_coords(envelope), EXTERIOR_TRANSPORT_MARGIN_CELLS)
    bbox_cells = cells_in_bbox(bb)
    field_in_bbox = complete_map.field_cells & bbox_cells
    nodes = bbox_cells - field_in_bbox
    placeable = _connected_component_from_start(route_probe_start, nodes=nodes)
    return ExteriorTransportDomain(
        search_bbox=bb,
        blocked_field_cells=field_in_bbox,
        placeable_cells=placeable,
    )


def _connected_component_from_start(start: Coord, *, nodes: frozenset[Coord]) -> frozenset[Coord]:
    if start not in nodes:
        return frozenset()
    seen: set[Coord] = {start}
    queue: deque[Coord] = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in neighbors4(current):
            if neighbor in seen or neighbor not in nodes:
                continue
            seen.add(neighbor)
            queue.append(neighbor)
    return frozenset(seen)


def build_weighted_transport_route_domain(
    *,
    complete_map: ReconstructionCompleteMap,
    anchor_abs: Coord,
    transport_entry_coord: Coord,
    transport_stub_cells: frozenset[Coord],
    route_goals: tuple[RouteGoal, ...],
    mining_occupied_cells: frozenset[Coord],
    incompatible_transport_cells: frozenset[Coord] | None = None,
    explicit_blocked_cells: frozenset[Coord] | None = None,
) -> WeightedTransportRouteDomain:
    envelope = frozenset(
        {
            anchor_abs,
            transport_entry_coord,
            *transport_stub_cells,
            *(goal.coord for goal in route_goals),
        }
    )
    bb = expand_bbox(bbox_from_coords(envelope), EXTERIOR_TRANSPORT_MARGIN_CELLS)
    candidate_cells = cells_in_bbox(bb)
    field_surface = complete_map.field_cells & candidate_cells
    exterior_surface = candidate_cells - complete_map.field_cells
    install_surface = field_surface | exterior_surface
    incompatible = incompatible_transport_cells or frozenset()
    explicit_blocked = explicit_blocked_cells or frozenset()
    walkable = install_surface - mining_occupied_cells - incompatible - explicit_blocked
    field_cost = complete_map.field_cells & walkable
    blocked = (mining_occupied_cells | incompatible | explicit_blocked) & candidate_cells
    return WeightedTransportRouteDomain(
        search_bbox=bb,
        blocked_cells=blocked,
        walkable_cells=walkable,
        field_cost_cells=field_cost,
    )


__all__ = [
    "EXTERIOR_TRANSPORT_MARGIN_CELLS",
    "build_exterior_transport_domain",
    "build_weighted_transport_route_domain",
]
