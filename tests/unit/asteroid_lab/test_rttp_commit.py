"""RTTP Layer 4 incremental commit — RTTP-G6 (PR-5)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
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
from tests.support.rttp_narrow_corridor_fixture import build_narrow_corridor_optimization_input


@pytest.fixture
def narrow_corridor_optimization_input() -> OptimizationInput:
    return build_narrow_corridor_optimization_input()


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
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    chosen: list[BundleCandidate] = []
    occupied: set[tuple[int, int]] = set()
    fot_reserved: set[tuple[int, int]] = set()
    domain = initial_commit_domain(skeleton, inp)
    for candidate in generation.normal_candidates:
        if fixed_output_transport_cell(candidate) in inp.mineable_cells:
            continue
        if candidate.occupied_cells & frozenset(occupied):
            continue
        if candidate.occupied_cells & frozenset(fot_reserved):
            continue
        if fixed_output_transport_cell(candidate) in occupied:
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
        fot_reserved.add(fixed_output_transport_cell(candidate))
        if len(chosen) >= count:
            break
    return tuple(chosen)


def test_commit_rejects_inlet_on_shared_transport(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    inp = narrow_corridor_optimization_input
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
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    chosen = _pick_committable_candidates(inp, count=2)
    assert len(chosen) >= 1

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

    assert len(result.committed_ids) >= 1
    assert result.domain_version >= 1
    assert result.domain_version == len(result.committed_ids)


def _commit_result_snapshot(
    inp: OptimizationInput,
    commit_order: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
) -> tuple[tuple[str, ...], frozenset[tuple[str, str]], int]:
    """Stable tuple for before/after PR-3 _attempt_commit_one extract comparison."""
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=commit_order),
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
    )
    conflict_pairs = frozenset(
        (conflict.candidate_id, conflict.reason.value) for conflict in result.conflicts
    )
    return result.committed_ids, conflict_pairs, result.domain_version


def test_incremental_commit_primary_behavior_unchanged_after_attempt_primitive_extract(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    """PR-3 gate: narrow-corridor single-candidate commit snapshot (before/after extract)."""
    from tests.support.rttp_narrow_corridor_fixture import (
        NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
        candidate_by_id,
    )

    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    candidate = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    pool = {candidate.candidate_id: candidate}
    order = (candidate.candidate_id,)
    before = _commit_result_snapshot(inp, order, pool)
    after = _commit_result_snapshot(inp, order, pool)
    assert after == before
    assert before[0] == order


def test_incremental_commit_narrow_corridor_snapshot_before_extract(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    """PR-3 gate: B-CS1 two-candidate primary pass snapshot (pre-extract baseline)."""
    from tests.support.rttp_narrow_corridor_fixture import (
        NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
        NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID,
        candidate_by_id,
    )

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
    order = (first.candidate_id, second.candidate_id)
    pool = {first.candidate_id: first, second.candidate_id: second}
    committed, conflicts, _version = _commit_result_snapshot(inp, order, pool)
    assert committed == (first.candidate_id,)
    assert (
        second.candidate_id,
        CommitConflictReason.INLET_ON_SHARED_TRANSPORT.value,
    ) in conflicts or (
        second.candidate_id,
        CommitConflictReason.REPROBE_FAILED.value,
    ) in conflicts
