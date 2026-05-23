"""RTTP Layer 3 greedy-regret selection — RTTP-G4 (PR-4)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    SelectionConfig,
    select_genome,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


def _pattern_by_id(pattern_id: str):
    for pattern in build_pattern_library():
        if pattern.pattern_id == pattern_id:
            return pattern
    msg = f"pattern not found: {pattern_id!r}"
    raise AssertionError(msg)


def _translate(anchor: tuple[int, int], offset: tuple[int, int]) -> tuple[int, int]:
    return (anchor[0] + offset[0], anchor[1] + offset[1])


def _bundle_candidate(
    anchor: tuple[int, int],
    *,
    pattern_id: str = "lin_e_len0",
    throughput_factor: int | None = None,
    route_probe_cost: int = 5,
) -> BundleCandidate:
    pattern = _pattern_by_id(pattern_id)
    occupied = frozenset(_translate(anchor, offset) for offset in pattern.occupied_offsets)
    output_stub = _translate(anchor, pattern.output_stub_offset)
    throughput = throughput_factor if throughput_factor is not None else pattern.throughput_factor
    return BundleCandidate(
        candidate_id=f"{anchor[0]},{anchor[1]}:{pattern.pattern_id}:shape_belt",
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=output_stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=throughput,
        route_probe_cost=route_probe_cost,
        reachable=True,
    )


def _skeleton_with_goals(
    greenfield_optimization_input: OptimizationInput,
    capacity_goals: int,
) -> RttpSkeleton:
    skeleton = RttpSkeletonBuilder.build(
        greenfield_optimization_input,
        config=RttpSkeletonConfig(),
    )
    return replace(skeleton, capacity_goals=capacity_goals)


def test_regret_prefers_high_scarcity_candidate(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    anchor_scarce = (5, 5)
    anchor_crowded = (8, 8)
    scarce_best = _bundle_candidate(anchor_scarce, throughput_factor=8, route_probe_cost=5)
    crowded_best = _bundle_candidate(anchor_crowded, throughput_factor=8, route_probe_cost=4)

    candidates = (
        scarce_best,
        _bundle_candidate(anchor_scarce, pattern_id="lin_n_len0", route_probe_cost=5),
        crowded_best,
        _bundle_candidate(
            anchor_crowded,
            pattern_id="lin_s_len0",
            throughput_factor=8,
            route_probe_cost=5,
        ),
        _bundle_candidate(
            anchor_crowded,
            pattern_id="lin_w_len0",
            throughput_factor=8,
            route_probe_cost=6,
        ),
    )
    skeleton = _skeleton_with_goals(greenfield_optimization_input, capacity_goals=1)
    config = SelectionConfig(lambda_regret=50.0)

    genome = select_genome(candidates, skeleton, greenfield_optimization_input, config=config)

    assert genome.commit_order[0] == scarce_best.candidate_id


def test_commit_order_is_explicit_not_rim_scan(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    skeleton = _skeleton_with_goals(inp, capacity_goals=4)
    rim_scan = tuple(sorted(inp.rim_cells))

    candidates = (
        _bundle_candidate((5, 5), throughput_factor=4, route_probe_cost=20),
        _bundle_candidate((8, 8), throughput_factor=16, route_probe_cost=1),
        _bundle_candidate((5, 8), throughput_factor=12, route_probe_cost=2),
        _bundle_candidate((8, 5), throughput_factor=8, route_probe_cost=3),
        _bundle_candidate((6, 5), throughput_factor=4, route_probe_cost=4),
    )
    genome = select_genome(
        candidates,
        skeleton,
        inp,
        config=SelectionConfig(lambda_regret=0.0),
    )

    assert isinstance(genome, PlacementGenome)
    assert len(genome.commit_order) >= 3

    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    selected_anchors = tuple(by_id[cid].anchor_coord for cid in genome.commit_order)
    rim_prefix = tuple(rim_scan[index] for index in range(len(selected_anchors)))

    assert selected_anchors != rim_prefix
