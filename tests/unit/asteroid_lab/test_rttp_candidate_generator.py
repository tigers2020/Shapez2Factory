"""RTTP Layer 2 candidate generator — RTTP-G3 (PR-3)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    CandidateRejectReason,
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


def test_candidate_generator_does_not_commit(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    before = replace(inp)
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    skeleton_before = replace(skeleton)

    generate_candidates(inp, skeleton, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)

    assert inp == before
    assert skeleton == skeleton_before


def test_interior_and_rim_unreachable_goes_to_rejected(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = replace(greenfield_with_catalog, route_goals=())
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    skeleton = replace(
        skeleton,
        ring_ports=(),
        lift_columns=(),
        trunk_mask_cells=frozenset(),
    )
    result = generate_candidates(inp, skeleton, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)

    assert result.normal_candidates == ()
    assert result.rejected_candidates
    assert any(
        rejected.rejection_reason is CandidateRejectReason.NOT_REACHABLE
        for rejected in result.rejected_candidates
    )


def test_reachable_candidate_in_normal_pool(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(inp, skeleton, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)

    assert len(result.normal_candidates) >= 1
    assert all(candidate.reachable for candidate in result.normal_candidates)
