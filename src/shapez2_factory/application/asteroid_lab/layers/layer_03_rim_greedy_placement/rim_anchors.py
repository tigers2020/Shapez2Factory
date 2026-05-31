"""Ordered outer-rim anchors (boundary traversal)."""

from __future__ import annotations

from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.cardinal_map import (  # noqa: E501
    CARDINAL_DIR_DELTA,
    CARDINAL_ORDER,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.rim_topology import field_rim_cells

DEGRADED_BOUNDARY_ORDER_SEGMENT = "DEGRADED_BOUNDARY_ORDER"

_DIR_DELTA = CARDINAL_DIR_DELTA
_CARDINAL_ORDER = CARDINAL_ORDER
_LEFT_TURN = {"E": "N", "N": "W", "W": "S", "S": "E"}
_RIGHT_TURN = {"E": "S", "S": "W", "W": "N", "N": "E"}


def _void_dirs_for_anchor(
    coord: Coord,
    *,
    field_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord],
) -> tuple[str, ...]:
    x, y = coord
    dirs: list[str] = []
    for name in _CARDINAL_ORDER:
        dx, dy = _DIR_DELTA[name]
        neighbor = (x + dx, y + dy)
        if neighbor not in field_cells and neighbor in external_void_cells:
            dirs.append(name)
    return tuple(dirs)


def _dir_from_to(origin: Coord, target: Coord) -> str | None:
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    for name, (ddx, ddy) in _DIR_DELTA.items():
        if dx == ddx and dy == ddy:
            return name
    return None


def _boundary_walk_cw(
    rim_cells: frozenset[Coord],
    *,
    start: Coord,
) -> tuple[list[Coord], bool]:
    """Clockwise walk on rim graph; interior on left. Returns (order, used_degraded_tail)."""
    rim_set = set(rim_cells)
    if start not in rim_set:
        return [], False

    ordered: list[Coord] = [start]
    visited: set[Coord] = {start}
    current = start
    prev: Coord = (start[0] - 1, start[1])
    incoming = _dir_from_to(prev, current)
    if incoming is None:
        incoming = "E"

    while len(ordered) < len(rim_set):
        options = (incoming, _LEFT_TURN[incoming], _RIGHT_TURN[incoming])
        next_cell: Coord | None = None
        next_incoming: str | None = None
        for direction in options:
            dx, dy = _DIR_DELTA[direction]
            candidate = (current[0] + dx, current[1] + dy)
            if candidate in rim_set and candidate not in visited:
                next_cell = candidate
                next_incoming = direction
                break
        if next_cell is None:
            break
        ordered.append(next_cell)
        visited.add(next_cell)
        prev, current = current, next_cell
        incoming = next_incoming or incoming

    used_degraded = len(ordered) < len(rim_set)
    if used_degraded:
        visited = set(ordered)
        tail = sorted(rim_set - visited, key=lambda c: (c[1], c[0]))
        ordered.extend(tail)
    return ordered, used_degraded


def _pick_walk_start(rim_cells: frozenset[Coord]) -> Coord:
    """Top-left-ish: max y, then min x (CW_TL baseline)."""
    return max(rim_cells, key=lambda c: (c[1], -c[0]))


@dataclass(frozen=True, slots=True)
class RimAnchor:
    coord: Coord
    void_dirs: tuple[str, ...]
    traversal_index: int
    rim_segment_id: str | int


def build_ordered_outer_rim_anchors(
    complete_map: ReconstructionCompleteMap,
) -> tuple[RimAnchor, ...]:
    """Boundary-walk order over field rim cells with exterior void normals only."""
    field_cells = complete_map.field_cells
    external_void = complete_map.external_void_cells
    rim = field_rim_cells(field_cells)
    rim_with_void = frozenset(
        coord
        for coord in rim
        if _void_dirs_for_anchor(
            coord,
            field_cells=field_cells,
            external_void_cells=external_void,
        )
    )
    if not rim_with_void:
        return ()

    start = _pick_walk_start(rim_with_void)
    ordered_coords, degraded = _boundary_walk_cw(rim_with_void, start=start)
    segment_id: str | int = "rim0" if not degraded else DEGRADED_BOUNDARY_ORDER_SEGMENT

    return tuple(
        RimAnchor(
            coord=coord,
            void_dirs=_void_dirs_for_anchor(
                coord,
                field_cells=field_cells,
                external_void_cells=external_void,
            ),
            traversal_index=index,
            rim_segment_id=segment_id,
        )
        for index, coord in enumerate(ordered_coords)
    )


__all__ = [
    "DEGRADED_BOUNDARY_ORDER_SEGMENT",
    "RimAnchor",
    "build_ordered_outer_rim_anchors",
]
