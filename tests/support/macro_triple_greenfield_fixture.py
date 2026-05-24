"""Deterministic greenfield fixture for RTTP MacroBundleT3 compiler/probe tests (PR-B)."""

from __future__ import annotations

from dataclasses import dataclass, replace

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RouteGoal,
    RouteGoalKind,
    RttpSkeletonConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder

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


def build_macro_triple_greenfield_input() -> OptimizationInput:
    """Minimal 4×4 mineable block (same geometry as unit-test greenfield)."""

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


def _bundle(
    candidate_id: str,
    anchor: Coord,
    *,
    occupied: frozenset[Coord] | None = None,
) -> BundleCandidate:
    pattern = build_pattern_library()[0]
    anchor_occupied = occupied or frozenset({anchor, (anchor[0] + 1, anchor[1])})
    output_stub = (anchor[0] + 2, anchor[1])
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=anchor_occupied,
        output_stub=output_stub,
        output_dir="E",
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=pattern.throughput_factor,
        route_probe_cost=1,
        reachable=True,
    )


def build_valid_macro_triple_candidates() -> tuple[
    BundleCandidate,
    BundleCandidate,
    BundleCandidate,
]:
    """Three non-overlapping rim anchors on the west edge."""

    return (
        _bundle("5,5:lin_e_len0:shape_belt", (5, 5), occupied=frozenset({(5, 5)})),
        _bundle("5,7:lin_e_len0:shape_belt", (5, 7), occupied=frozenset({(5, 7)})),
        _bundle("8,5:lin_e_len0:shape_belt", (8, 5), occupied=frozenset({(8, 5)})),
    )


def build_overlapping_macro_triple_candidates() -> (
    tuple[BundleCandidate, BundleCandidate, BundleCandidate]
):
    """Three candidates sharing occupied cell (5, 6)."""

    return (
        _bundle("5,5:lin_e_len0:shape_belt", (5, 5), occupied=frozenset({(5, 5), (5, 6)})),
        _bundle("5,7:lin_e_len0:shape_belt", (5, 7), occupied=frozenset({(5, 6), (5, 7)})),
        _bundle("8,5:lin_e_len0:shape_belt", (8, 5), occupied=frozenset({(8, 5)})),
    )


@dataclass(frozen=True, slots=True)
class MacroTripleGreenfieldFixture:
    inp: OptimizationInput
    skeleton: RttpSkeleton
    valid_triple: tuple[BundleCandidate, BundleCandidate, BundleCandidate]


def build_macro_triple_greenfield_fixture() -> MacroTripleGreenfieldFixture:
    inp = build_macro_triple_greenfield_input()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    return MacroTripleGreenfieldFixture(
        inp=inp,
        skeleton=skeleton,
        valid_triple=build_valid_macro_triple_candidates(),
    )


def build_unreachable_shared_trunk_skeleton(
    fixture: MacroTripleGreenfieldFixture,
) -> RttpSkeleton:
    """Skeleton without lift columns — shared lift plan cannot be derived/reached."""

    return replace(
        fixture.skeleton,
        lift_columns=(),
    )


__all__ = [
    "MacroTripleGreenfieldFixture",
    "build_macro_triple_greenfield_fixture",
    "build_macro_triple_greenfield_input",
    "build_overlapping_macro_triple_candidates",
    "build_unreachable_shared_trunk_skeleton",
    "build_valid_macro_triple_candidates",
]
