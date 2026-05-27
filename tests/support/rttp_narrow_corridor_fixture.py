"""Deterministic narrow-corridor ``OptimizationInput`` for RTTP Sequence 10A regressions."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)
from tests.support.catalog_test_fixtures import build_minimal_test_catalog_slice

# Stable catalog-native candidate IDs for B-CS1 / Sequence 10A (``bv:1`` minimal slice).
# Stable under FixedOutputTransportPolicy.OUTSIDE_MINEABLE (FOT off mineable).
NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID = "7,5:cat_bv_1_S_ext0:shape_belt"
NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID = "7,9:cat_bv_1_N_ext0:shape_belt"
NARROW_CORRIDOR_PROTECTED_CANDIDATE_ID = "5,5:cat_bv_1_E_ext0:shape_belt"

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
        catalog_slice=build_minimal_test_catalog_slice(),
    )


def candidate_by_id(generation, candidate_id: str):
    """Return a normal-pool candidate by stable catalog-native ``candidate_id``."""

    from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
        CandidateGenerationResult,
    )

    if not isinstance(generation, CandidateGenerationResult):
        msg = "generation must be CandidateGenerationResult"
        raise TypeError(msg)
    for candidate in generation.normal_candidates:
        if candidate.candidate_id == candidate_id:
            return candidate
    msg = f"candidate not found: {candidate_id}"
    raise AssertionError(msg)


__all__ = [
    "NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID",
    "NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID",
    "NARROW_CORRIDOR_PROTECTED_CANDIDATE_ID",
    "build_narrow_corridor_optimization_input",
    "candidate_by_id",
]
