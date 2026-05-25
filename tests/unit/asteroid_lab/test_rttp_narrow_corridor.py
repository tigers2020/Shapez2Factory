"""RTTP Sequence 10A — narrow corridor regression fixtures."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from tests.support.rttp_narrow_corridor_fixture import (
    NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
    NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID,
    NARROW_CORRIDOR_PROTECTED_CANDIDATE_ID,
    build_narrow_corridor_optimization_input,
    candidate_by_id,
)


@pytest.fixture
def narrow_corridor_optimization_input() -> OptimizationInput:
    return build_narrow_corridor_optimization_input()


def test_narrow_corridor_probe_vs_commit_regression(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    """Generation-time reachability must not imply commit-time reachability (RTTP-G6)."""

    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )

    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    assert first.reachable is True
    assert second.reachable is True
    assert not (first.occupied_cells & second.occupied_cells)

    domain = initial_commit_domain(skeleton, inp)
    pair_result = incremental_commit(
        PlacementGenome(
            commit_order=(first.candidate_id, second.candidate_id),
        ),
        {
            first.candidate_id: first,
            second.candidate_id: second,
        },
        inp,
        skeleton,
        domain=domain,
    )

    assert first.candidate_id in pair_result.committed_ids
    assert second.candidate_id not in pair_result.committed_ids
    assert any(
        conflict.candidate_id == second.candidate_id
        and conflict.reason
        in (
            CommitConflictReason.REPROBE_FAILED,
            CommitConflictReason.INLET_ON_SHARED_TRANSPORT,
            CommitConflictReason.ROUTE_CELL_CONFLICT,
        )
        for conflict in pair_result.conflicts
    )


def test_narrow_corridor_protected_bridge_regression(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    """Routes through protected corridor cells must fail commit with enum reason."""

    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.ALLOW,
    )
    candidate = candidate_by_id(generation, NARROW_CORRIDOR_PROTECTED_CANDIDATE_ID)
    domain = initial_commit_domain(skeleton, inp)

    result = incremental_commit(
        PlacementGenome(commit_order=(candidate.candidate_id,)),
        {candidate.candidate_id: candidate},
        inp,
        skeleton,
        domain=domain,
    )

    assert candidate.candidate_id not in result.committed_ids
    assert any(
        conflict.candidate_id == candidate.candidate_id
        and conflict.reason
        in (
            CommitConflictReason.HARD_PROTECTED_CONFLICT,
            CommitConflictReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE,
            CommitConflictReason.REPROBE_FAILED,
        )
        for conflict in result.conflicts
    )


def test_narrow_corridor_pipeline_deterministic(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    first = run_rttp_pipeline(
        narrow_corridor_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    second = run_rttp_pipeline(
        narrow_corridor_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )

    assert first == second
    assert first.validation_passed
    assert len(first.commit_result.committed_ids) >= 1
