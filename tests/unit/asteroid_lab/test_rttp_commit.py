"""RTTP Layer 4 incremental commit — RTTP-G6 (PR-5)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    ExtractorPlacementPolicy,
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
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


def _pick_committable_candidates(
    inp: OptimizationInput,
    *,
    count: int,
) -> tuple[BundleCandidate, ...]:
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    chosen: list[BundleCandidate] = []
    occupied: set[tuple[int, int]] = set()
    domain = initial_commit_domain(skeleton, inp)
    for candidate in generation.normal_candidates:
        if candidate.occupied_cells & frozenset(occupied):
            continue
        trial = incremental_commit(
            PlacementGenome(commit_order=(candidate.candidate_id,)),
            {candidate.candidate_id: candidate},
            inp,
            skeleton,
            domain=domain,
        )
        if candidate.candidate_id not in trial.committed_ids:
            continue
        chosen.append(candidate)
        occupied.update(candidate.occupied_cells)
        if len(chosen) >= count:
            break
    return tuple(chosen)


def test_commit_rejects_inlet_on_shared_transport(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    committable = _pick_committable_candidates(inp, count=1)
    assert committable, "expected at least one committable candidate"
    first = committable[0]
    domain = initial_commit_domain(skeleton, inp)

    solo = incremental_commit(
        PlacementGenome(commit_order=(first.candidate_id,)),
        {first.candidate_id: first},
        inp,
        skeleton,
        domain=domain,
    )
    assert first.candidate_id in solo.committed_ids
    shared_transport = next(iter(solo.reserved_route_cells))

    others = _pick_committable_candidates(inp, count=3)
    second_base = next(
        (item for item in others if item.candidate_id != first.candidate_id),
        None,
    )
    assert second_base is not None
    second = replace(
        second_base,
        candidate_id=f"conflict:{second_base.candidate_id}",
        output_stub=shared_transport,
    )
    candidates_by_id = {first.candidate_id: first, second.candidate_id: second}
    result = incremental_commit(
        PlacementGenome(commit_order=(first.candidate_id, second.candidate_id)),
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
    )

    assert first.candidate_id in result.committed_ids
    assert second.candidate_id not in result.committed_ids
    assert any(
        conflict.candidate_id == second.candidate_id
        and conflict.reason is CommitConflictReason.INLET_ON_SHARED_TRANSPORT
        for conflict in result.conflicts
    )


def test_commit_reprobes_latest_domain(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    chosen = _pick_committable_candidates(inp, count=2)
    assert len(chosen) >= 2

    candidates_by_id = {item.candidate_id: item for item in chosen}
    genome = PlacementGenome(commit_order=tuple(item.candidate_id for item in chosen))
    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        genome,
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
    )

    assert len(result.committed_ids) >= 2
    assert result.domain_version >= 2
    assert result.domain_version == len(result.committed_ids)
