"""Bounded deferred commit retry execution after primary incremental_commit (PR-3)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence

from django_apps.asteroid_lab.contracts.deferred_retry_execute import DeferredRetryExecuteResult
from django_apps.asteroid_lab.contracts.deferred_retry_shadow import DeferredRetryShadowConfig
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.commit.deferred_retry_shadow import (
    _eligible_conflicts,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflict,
    CommitConflictReason,
    CommitResult,
    _attempt_commit_one,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def merged_committed_ids_for_genome_order(
    *,
    commit_order: Sequence[str],
    primary_committed_ids: Sequence[str],
    recovered_candidate_ids: Sequence[str],
) -> tuple[str, ...]:
    """All committed ids sorted by genome ``commit_order`` (PR-3 merge contract)."""

    committed = frozenset(primary_committed_ids) | frozenset(recovered_candidate_ids)
    return tuple(candidate_id for candidate_id in commit_order if candidate_id in committed)


def _eligible_queue(
    *,
    primary_commit_result: CommitResult,
    commit_order: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
    config: DeferredRetryShadowConfig,
) -> tuple[str, ...]:
    order_index = {candidate_id: index for index, candidate_id in enumerate(commit_order)}
    eligible_conflicts = _eligible_conflicts(primary_commit_result.conflicts)
    rows: list[tuple[int, str]] = []
    for conflict in eligible_conflicts:
        index = order_index.get(conflict.candidate_id)
        if index is None:
            continue
        if conflict.candidate_id not in candidates_by_id:
            continue
        rows.append((index, conflict.candidate_id))
    rows.sort()
    candidate_ids = [candidate_id for _, candidate_id in rows]
    if config.max_candidates is not None and len(candidate_ids) > config.max_candidates:
        candidate_ids = candidate_ids[: config.max_candidates]
    return tuple(candidate_ids)


def _apply_confirmed(
    *,
    candidate: BundleCandidate,
    route_cells: frozenset,
    committed_occupied: frozenset,
    committed_route_cells: frozenset,
    trunk_mask_cells: frozenset,
    domain_version: int,
) -> tuple[frozenset, frozenset, frozenset, int]:
    new_occupied = frozenset(committed_occupied | candidate.occupied_cells)
    new_route_cells = frozenset(committed_route_cells | route_cells)
    new_trunk = frozenset(trunk_mask_cells | route_cells)
    return new_occupied, new_route_cells, new_trunk, domain_version + 1


def _state_after_primary(
    *,
    primary_commit_result: CommitResult,
    commit_order: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
) -> tuple[frozenset, frozenset, int]:
    """Rebuild commit-time state from primary ``CommitResult`` (no re-probe)."""

    primary_committed = frozenset(primary_commit_result.committed_ids)
    occupied: set[object] = set()
    for candidate_id in commit_order:
        if candidate_id not in primary_committed:
            continue
        candidate = candidates_by_id[candidate_id]
        occupied.update(candidate.occupied_cells)
    return (
        frozenset(occupied),
        primary_commit_result.reserved_route_cells,
        primary_commit_result.domain_version,
    )


def _merge_conflicts(
    *,
    primary_commit_result: CommitResult,
    recovered_candidate_ids: frozenset[str],
    retry_failures: tuple[CommitConflict, ...],
) -> tuple[CommitConflict, ...]:
    """Drop superseded eligible REPROBE_FAILED rows; append deferred failure rows."""
    retry_failed_ids = frozenset(conflict.candidate_id for conflict in retry_failures)
    superseded_reprobe_ids = recovered_candidate_ids | retry_failed_ids
    kept_primary = tuple(
        conflict
        for conflict in primary_commit_result.conflicts
        if not (
            conflict.reason is CommitConflictReason.REPROBE_FAILED
            and conflict.candidate_id in superseded_reprobe_ids
        )
    )
    return kept_primary + retry_failures


def run_bounded_deferred_retry(
    *,
    primary_commit_result: CommitResult,
    commit_order: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    config: DeferredRetryShadowConfig,
) -> DeferredRetryExecuteResult:
    """One-round deferred retry on latest domain after primary commits (no rollback)."""

    eligible_ids = _eligible_queue(
        primary_commit_result=primary_commit_result,
        commit_order=commit_order,
        candidates_by_id=candidates_by_id,
        config=config,
    )
    if not eligible_ids:
        return DeferredRetryExecuteResult(
            merged_commit_result=primary_commit_result,
            deferred_retry_rounds_executed=0,
            deferred_retry_eligible_count=0,
            deferred_retry_attempted_count=0,
            deferred_retry_recovered_count=0,
            deferred_retry_still_failed_count=0,
            recovered_candidate_ids=(),
            deferred_retry_failed_reason_counts={},
        )

    goals = probe_goal_coords(inp, skeleton)
    committed_occupied, committed_route_cells, domain_version = _state_after_primary(
        primary_commit_result=primary_commit_result,
        commit_order=commit_order,
        candidates_by_id=candidates_by_id,
    )

    recovered: list[str] = []
    retry_failures: list[CommitConflict] = []
    reason_counts: Counter[str] = Counter()

    for candidate_id in eligible_ids:
        candidate = candidates_by_id[candidate_id]
        outcome = _attempt_commit_one(
            candidate,
            skeleton=skeleton,
            inp=inp,
            goals=goals,
            committed_occupied=committed_occupied,
            committed_route_cells=committed_route_cells,
            max_expansions=config.route_probe_max_expansions,
        )
        if outcome.committed:
            recovered.append(candidate_id)
            committed_occupied, committed_route_cells, _, domain_version = _apply_confirmed(
                candidate=candidate,
                route_cells=outcome.route_cells,
                committed_occupied=committed_occupied,
                committed_route_cells=committed_route_cells,
                trunk_mask_cells=frozenset(),
                domain_version=domain_version,
            )
            continue
        if outcome.conflict is not None:
            retry_failures.append(outcome.conflict)
            reason_counts[outcome.conflict.reason.value] += 1

    recovered_ids = tuple(recovered)
    attempted_count = len(eligible_ids)
    recovered_count = len(recovered_ids)
    merged_committed_ids = merged_committed_ids_for_genome_order(
        commit_order=commit_order,
        primary_committed_ids=primary_commit_result.committed_ids,
        recovered_candidate_ids=recovered_ids,
    )
    merged = CommitResult(
        committed_ids=merged_committed_ids,
        reserved_route_cells=committed_route_cells,
        domain_version=domain_version,
        conflicts=_merge_conflicts(
            primary_commit_result=primary_commit_result,
            recovered_candidate_ids=frozenset(recovered_ids),
            retry_failures=tuple(retry_failures),
        ),
    )
    return DeferredRetryExecuteResult(
        merged_commit_result=merged,
        deferred_retry_rounds_executed=1,
        deferred_retry_eligible_count=len(eligible_ids),
        deferred_retry_attempted_count=attempted_count,
        deferred_retry_recovered_count=recovered_count,
        deferred_retry_still_failed_count=attempted_count - recovered_count,
        recovered_candidate_ids=recovered_ids,
        deferred_retry_failed_reason_counts=dict(reason_counts),
    )


__all__ = [
    "merged_committed_ids_for_genome_order",
    "run_bounded_deferred_retry",
]
