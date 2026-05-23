"""Fixtures for asteroid_lab unit tests (RTTP optimization)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
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


@pytest.fixture
def greenfield_optimization_input() -> OptimizationInput:
    """Minimal greenfield map: 4×4 mineable block (16 cells), empty trunk/protected."""

    mineable = frozenset((x, y) for x in range(5, 9) for y in range(5, 9))
    rim = _perimeter_cells(mineable)
    inner = mineable - rim
    return OptimizationInput(
        mineable_cells=mineable,
        rim_cells=rim,
        inner_cells=inner,
        external_void_cells=_external_void_ring(mineable),
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=frozenset(),
        transport_kind=TransportKind.SHAPE_BELT,
    )
