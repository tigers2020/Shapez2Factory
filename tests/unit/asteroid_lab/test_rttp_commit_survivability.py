"""RTTP B-CS1 — commit survivability contract (Axis B).

Invariant: normal-pool candidate.reachable is NOT commit proof.
Commit must re-probe on latest rebuilt route_domain (incremental_commit.py).
"""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    incremental_commit,
    initial_commit_domain,
    probe_route,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from tests.support.rttp_narrow_corridor_fixture import (
    build_narrow_corridor_optimization_input,
)

_PROBE_FIRST = "5,5:lin_e_len3:shape_belt"
_PROBE_SECOND = "5,6:lin_n_len0:shape_belt"


@pytest.fixture
def narrow_corridor_optimization_input() -> OptimizationInput:
    return build_narrow_corridor_optimization_input()


def _candidate_by_id(generation, candidate_id: str):
    for candidate in generation.normal_candidates:
        if candidate.candidate_id == candidate_id:
            return candidate
    msg = f"candidate not found: {candidate_id}"
    raise AssertionError(msg)


def test_b_cs1_module_imports() -> None:
    assert CommitConflictReason.REPROBE_FAILED.value == "reprobe_failed"
    assert build_narrow_corridor_optimization_input() is not None


def test_normal_pool_reachable_is_not_commit_proof(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    """B-CS1: both in normal pool with reachable=True; second fails commit reprobe."""

    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    first = _candidate_by_id(generation, _PROBE_FIRST)
    second = _candidate_by_id(generation, _PROBE_SECOND)

    assert first.reachable is True
    assert second.reachable is True

    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=(first.candidate_id, second.candidate_id)),
        {first.candidate_id: first, second.candidate_id: second},
        inp,
        skeleton,
        domain=domain,
    )

    assert first.candidate_id in result.committed_ids
    assert second.candidate_id not in result.committed_ids
    assert any(
        conflict.candidate_id == second.candidate_id
        and conflict.reason is CommitConflictReason.REPROBE_FAILED
        for conflict in result.conflicts
    )


def test_commit_ignores_stale_generation_reachable_flag(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    """Even if reachable=True on DTO, commit uses fresh probe on latest domain."""

    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    first = _candidate_by_id(generation, _PROBE_FIRST)
    second = _candidate_by_id(generation, _PROBE_SECOND)

    stale_second = replace(
        second,
        reachable=True,
        route_probe_cost=0,
    )
    assert stale_second.reachable is True

    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        PlacementGenome(
            commit_order=(first.candidate_id, stale_second.candidate_id),
        ),
        {first.candidate_id: first, stale_second.candidate_id: stale_second},
        inp,
        skeleton,
        domain=domain,
    )

    assert stale_second.candidate_id not in result.committed_ids
    assert any(
        conflict.candidate_id == stale_second.candidate_id
        and conflict.reason is CommitConflictReason.REPROBE_FAILED
        for conflict in result.conflicts
    )


def test_incremental_commit_invokes_probe_route_per_candidate(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    """B-CS1: commit loop must call probe_route (latest domain), not only read DTO."""

    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    assert generation.normal_candidates
    candidate = generation.normal_candidates[0]
    domain = initial_commit_domain(skeleton, inp)

    patch_target = "django_apps.asteroid_lab.optimization.commit.incremental_commit.probe_route"
    with patch(patch_target, wraps=probe_route) as spy:
        incremental_commit(
            PlacementGenome(commit_order=(candidate.candidate_id,)),
            {candidate.candidate_id: candidate},
            inp,
            skeleton,
            domain=domain,
        )

    assert spy.call_count >= 1


def test_incremental_commit_rolls_back_unreachable_candidate(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    """Documented name in asteroid_lab_07 — delegates to B-CS1 contract."""

    test_normal_pool_reachable_is_not_commit_proof(narrow_corridor_optimization_input)
