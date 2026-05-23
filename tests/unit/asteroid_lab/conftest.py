"""Fixtures for asteroid_lab unit tests (RTTP optimization)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)


def _perimeter_cells(block: frozenset[Coord]) -> frozenset[Coord]:
    neighbors4 = ((0, 1), (0, -1), (1, 0), (-1, 0))
    return frozenset(
        coord
        for coord in block
        if any((coord[0] + dx, coord[1] + dy) not in block for dx, dy in neighbors4)
    )


def _external_void_ring(mineable: frozenset[Coord]) -> frozenset[Coord]:
    neighbors4 = ((0, 1), (0, -1), (1, 0), (-1, 0))
    void: set[Coord] = set()
    for coord in mineable:
        for dx, dy in neighbors4:
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
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
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


@pytest.fixture
def greenfield_optimization_input() -> OptimizationInput:
    """Minimal greenfield map: 4×4 mineable block (16 cells), empty trunk/protected."""

    mineable = frozenset((x, y) for x in range(5, 9) for y in range(5, 9))
    rim = _perimeter_cells(mineable)
    inner = mineable - rim
    external_void = _external_void_ring(mineable)
    return OptimizationInput(
        mineable_cells=mineable,
        rim_cells=rim,
        inner_cells=inner,
        external_void_cells=external_void,
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=frozenset(),
        transport_kind=TransportKind.SHAPE_BELT,
        route_goals=_external_margin_goals(rim, external_void),
        existing_transport_cells=frozenset(),
    )
