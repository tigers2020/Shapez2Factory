"""RTTP P1 map class ??existing trunk from reconstruction (PR-6)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


def _existing_trunk_optimization_input() -> OptimizationInput:
    from tests.support.rttp_narrow_corridor_fixture import (
        build_narrow_corridor_optimization_input,
    )

    return build_narrow_corridor_optimization_input()


def test_skeleton_includes_existing_trunk_cells() -> None:
    inp = _existing_trunk_optimization_input()

    assert inp.blocked_incompatible_transport_cells == frozenset()
    assert inp.existing_trunk_cells

    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())

    assert inp.existing_trunk_cells <= skeleton.trunk_mask_cells
    assert inp.existing_trunk_cells.issubset(skeleton.trunk_mask_cells)


def test_reachable_candidate_attaches_to_existing_trunk() -> None:
    inp = _existing_trunk_optimization_input()

    assert inp.existing_trunk_cells
    assert inp.route_goals
    assert inp.transport_kind is TransportKind.SHAPE_BELT

    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(inp, skeleton, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)

    assert len(result.normal_candidates) >= 1
    assert any(candidate.reachable for candidate in result.normal_candidates)


def test_existing_trunk_pipeline_commits_deterministically() -> None:
    """P1 map class: full pipeline (select → commit) on reconstruction-seeded trunk."""

    inp = _existing_trunk_optimization_input()
    first = run_rttp_pipeline(inp, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)
    second = run_rttp_pipeline(inp, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)

    assert first.normal_count >= 1
    assert len(first.commit_result.committed_ids) >= 1
    assert first.structural_validation_passed
    assert first.validation_passed is False
    assert first.run_status == "partial_success"
    assert first == second
    assert first.commit_result.committed_ids == second.commit_result.committed_ids
    assert first.genome.commit_order == second.genome.commit_order
