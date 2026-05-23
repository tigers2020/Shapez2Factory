"""Deterministic narrow-corridor ``OptimizationInput`` for RTTP Sequence 10A regressions."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)

_NEIGHBORS4: tuple[tuple[int, int], ...] = ((0, 1), (0, -1), (1, 0), (-1, 0))


def _perimeter_cells(block: frozenset[Coord]) -> frozenset[Coord]:
    return frozenset(
        coord
        for coord in block
        if any((coord[0] + dx, coord[1] + dy) not in block for dx, dy in _NEIGHBORS4)
    )


def _external_void_ring(mineable: frozenset[Coord]) -> frozenset[Coord]:
    void: set[Coord] = set()
    for coord in mineable:
        for dx, dy in _NEIGHBORS4:
            neighbor = (coord[0] + dx, coord[1] + dy)
            if neighbor not in mineable:
                void.add(neighbor)
    return frozenset(void)


def _external_margin_goals(
    rim: frozenset[Coord],
    external_void: frozenset[Coord],
) -> tuple[RouteGoal, ...]:
    seen: set[Coord] = set()
    goals: list[RouteGoal] = []
    for rim_cell in sorted(rim):
        for dx, dy in _NEIGHBORS4:
            neighbor = (rim_cell[0] + dx, rim_cell[1] + dy)
            if neighbor not in external_void or neighbor in seen:
                continue
            seen.add(neighbor)
            goals.append(
                RouteGoal(
                    coord=neighbor,
                    goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
                    transport_kind=TransportKind.SHAPE_BELT,
                    priority=20,
                    existing_trunk=False,
                )
            )
    return tuple(goals)


def build_narrow_corridor_optimization_input() -> OptimizationInput:
    """5×5 mineable block with interior wall (x=7, y=6..8) and protected top bridge."""

    all_cells = frozenset((x, y) for x in range(5, 10) for y in range(5, 10))
    interior_wall = frozenset((7, y) for y in range(6, 9))
    mineable = all_cells - interior_wall
    rim = _perimeter_cells(mineable)
    inner = mineable - rim
    external_void = _external_void_ring(mineable)
    protected_bridge = frozenset({(6, 5), (7, 5), (8, 5)})

    return OptimizationInput(
        mineable_cells=mineable,
        rim_cells=rim,
        inner_cells=inner,
        external_void_cells=external_void,
        protected_corridor_cells=protected_bridge,
        existing_trunk_cells=frozenset({(4, 7)}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_goals=_external_margin_goals(rim, external_void),
        existing_transport_cells=frozenset(),
    )


__all__ = ["build_narrow_corridor_optimization_input"]
