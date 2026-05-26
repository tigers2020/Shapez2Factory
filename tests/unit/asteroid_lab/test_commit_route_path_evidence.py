"""EVTC-5 — commit-time route path evidence (output-only)."""

from __future__ import annotations

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
from django_apps.asteroid_lab.optimization.input_contracts import RttpSkeletonConfig
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from tests.support.rttp_narrow_corridor_fixture import (
    NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
    NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID,
    build_narrow_corridor_optimization_input,
    candidate_by_id,
)


def test_successful_commit_emits_stable_evidence() -> None:
    inp = build_narrow_corridor_optimization_input()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=(first.candidate_id,)),
        {first.candidate_id: first},
        inp,
        skeleton,
        domain=domain,
    )
    assert len(result.commit_route_evidence) == 1
    row = result.commit_route_evidence[0]
    assert row["candidate_id"] == first.candidate_id
    assert row["path_length"] >= 1
    assert row["reached_goal"] is not None
    assert isinstance(row["path_hash"], str) and len(row["path_hash"]) == 16

    repeat = incremental_commit(
        PlacementGenome(commit_order=(first.candidate_id,)),
        {first.candidate_id: first},
        inp,
        skeleton,
        domain=initial_commit_domain(skeleton, inp),
    )
    repeat_row = repeat.commit_route_evidence[0]
    assert repeat_row["path_hash"] == row["path_hash"]


def test_rolled_back_candidate_has_no_evidence_row() -> None:
    inp = build_narrow_corridor_optimization_input()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
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
    assert any(c.reason is CommitConflictReason.REPROBE_FAILED for c in result.conflicts) or any(
        c.candidate_id == second.candidate_id for c in result.conflicts
    )
    evidence_ids = {row["candidate_id"] for row in result.commit_route_evidence}
    assert second.candidate_id not in evidence_ids
    assert first.candidate_id in evidence_ids
