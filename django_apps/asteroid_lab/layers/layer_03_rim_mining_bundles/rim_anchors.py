"""Outer-rim anchor fieldward direction selection (R2-lite enumeration)."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.route_goal import RouteGoal
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.reconstruction.rim_topology import field_rim_cells
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_OFFSET_BY_DIRECTION: tuple[tuple[Direction, Coord], ...] = (
    (Direction.N, (0, -1)),
    (Direction.E, (1, 0)),
    (Direction.S, (0, 1)),
    (Direction.W, (-1, 0)),
)

_TIE_ORDER = {Direction.N: 0, Direction.E: 1, Direction.S: 2, Direction.W: 3}


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _exterior_cardinal_dirs(
    anchor: Coord,
    *,
    field_cells: frozenset[Coord],
) -> list[tuple[Direction, Coord]]:
    out: list[tuple[Direction, Coord]] = []
    for direction, (dx, dy) in _OFFSET_BY_DIRECTION:
        neighbor = (anchor[0] + dx, anchor[1] + dy)
        if neighbor not in field_cells:
            out.append((direction, neighbor))
    return out


def exterior_output_dir_candidates(
    anchor: Coord,
    *,
    complete_map: ReconstructionCompleteMap,
    route_goals: tuple[RouteGoal, ...],
    transport_kind: TransportKind,
) -> tuple[Direction, ...]:
    pairs = _exterior_cardinal_dirs(anchor, field_cells=complete_map.field_cells)
    if not pairs:
        return ()
    matching = [g for g in route_goals if g.transport_kind == transport_kind]

    def score(item: tuple[Direction, Coord]) -> tuple[int, int, int]:
        direction, void_coord = item
        if not matching:
            return (0, _TIE_ORDER[direction], 0)
        min_goal_dist = min(_manhattan(void_coord, g.coord) for g in matching)
        return (min_goal_dist, _TIE_ORDER[direction], 0)

    ordered = sorted(pairs, key=score)
    return tuple(d for d, _ in ordered)


def select_exterior_output_dir(
    anchor: Coord,
    *,
    complete_map: ReconstructionCompleteMap,
    route_goals: tuple[RouteGoal, ...],
    transport_kind: TransportKind,
) -> Direction | None:
    candidates = exterior_output_dir_candidates(
        anchor,
        complete_map=complete_map,
        route_goals=route_goals,
        transport_kind=transport_kind,
    )
    if not candidates:
        return None
    return candidates[0]


def sorted_outer_rim_anchors(field_cells: frozenset[Coord]) -> tuple[Coord, ...]:
    return tuple(sorted(field_rim_cells(field_cells), key=lambda c: (c[1], c[0])))


__all__ = [
    "exterior_output_dir_candidates",
    "select_exterior_output_dir",
    "sorted_outer_rim_anchors",
]
