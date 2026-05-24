"""Observe-only deferred commit retry shadow (PR-1)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.asteroid_lab.contracts.deferred_retry_shadow import (
    PRIMARY_INCREMENTAL_COMMIT_PHASE,
    DeferredRetryShadowBudget,
    DeferredRetryShadowCandidate,
    DeferredRetryShadowConfig,
    DeferredRetryShadowSummary,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflict,
    CommitConflictReason,
    CommitResult,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput


def _commits_before(
    candidate_id: str,
    commit_order: Sequence[str],
    committed_ids: frozenset[str],
) -> int:
    count = 0
    for cid in commit_order:
        if cid == candidate_id:
            break
        if cid in committed_ids:
            count += 1
    return count


def _eligible_conflicts(
    conflicts: tuple[CommitConflict, ...],
) -> tuple[CommitConflict, ...]:
    return tuple(
        conflict
        for conflict in conflicts
        if conflict.reason is CommitConflictReason.REPROBE_FAILED
    )


def build_deferred_retry_shadow_summary(
    *,
    primary_commit_result: CommitResult,
    commit_order: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
    inp: OptimizationInput,
    config: DeferredRetryShadowConfig | None = None,
) -> DeferredRetryShadowSummary:
    """Pure summary of deferred retry queue (no probe, no commit)."""

    resolved = config or DeferredRetryShadowConfig()
    if not resolved.enabled:
        empty_budget = DeferredRetryShadowBudget(
            max_retry_rounds=resolved.max_retry_rounds,
            max_candidates=0,
            route_probe_max_expansions=resolved.route_probe_max_expansions,
        )
        return DeferredRetryShadowSummary(
            enabled=False,
            observe_only=resolved.observe_only,
            source_phase=PRIMARY_INCREMENTAL_COMMIT_PHASE,
            candidate_count=0,
            candidates=(),
            budget=empty_budget,
            domain_context=_domain_context(
                primary_commit_result,
                inp,
                eligible_count=0,
            ),
            ineligible_conflict_count=len(primary_commit_result.conflicts),
        )

    committed_set = frozenset(primary_commit_result.committed_ids)
    order_index = {cid: idx for idx, cid in enumerate(commit_order)}
    eligible = _eligible_conflicts(primary_commit_result.conflicts)
    rows: list[DeferredRetryShadowCandidate] = []
    for conflict in eligible:
        idx = order_index.get(conflict.candidate_id)
        if idx is None:
            continue
        candidate = candidates_by_id.get(conflict.candidate_id)
        if candidate is None:
            continue
        rows.append(
            DeferredRetryShadowCandidate(
                candidate_id=conflict.candidate_id,
                conflict_reason=conflict.reason.value,
                original_commit_order=idx,
                transport_kind=candidate.transport_kind.value,
                domain_snapshot_index=_commits_before(
                    conflict.candidate_id,
                    commit_order,
                    committed_set,
                ),
                retry_round=0,
            )
        )
    rows.sort(key=lambda row: (row.original_commit_order, row.candidate_id))
    if resolved.max_candidates is not None and len(rows) > resolved.max_candidates:
        rows = rows[: resolved.max_candidates]
    budget = DeferredRetryShadowBudget(
        max_retry_rounds=resolved.max_retry_rounds,
        max_candidates=len(rows),
        route_probe_max_expansions=resolved.route_probe_max_expansions,
    )
    ineligible = len(primary_commit_result.conflicts) - len(eligible)
    return DeferredRetryShadowSummary(
        enabled=True,
        observe_only=resolved.observe_only,
        source_phase=PRIMARY_INCREMENTAL_COMMIT_PHASE,
        candidate_count=len(rows),
        candidates=tuple(rows),
        budget=budget,
        domain_context=_domain_context(
            primary_commit_result,
            inp,
            eligible_count=len(rows),
        ),
        ineligible_conflict_count=ineligible,
    )


def _domain_context(
    primary_commit_result: CommitResult,
    inp: OptimizationInput,
    *,
    eligible_count: int,
) -> dict[str, Any]:
    return {
        "primary_commit_domain_version": primary_commit_result.domain_version,
        "primary_committed_count": len(primary_commit_result.committed_ids),
        "primary_conflict_count": len(primary_commit_result.conflicts),
        "eligible_reprobe_failed_count": eligible_count,
        "transport_kind": inp.transport_kind.value,
    }


def deferred_retry_shadow_metrics(
    summary: DeferredRetryShadowSummary,
) -> dict[str, Any]:
    """JSON-serializable projection for algorithm_steps (output-only)."""

    return {
        "source_phase": summary.source_phase,
        "observe_only": summary.observe_only,
        "enabled": summary.enabled,
        "candidate_count": summary.candidate_count,
        "eligible_candidate_ids": [row.candidate_id for row in summary.candidates],
        "ineligible_conflict_count": summary.ineligible_conflict_count,
        "budget": {
            "max_retry_rounds": summary.budget.max_retry_rounds,
            "max_candidates": summary.budget.max_candidates,
            "route_probe_max_expansions": summary.budget.route_probe_max_expansions,
        },
        "domain_context": dict(summary.domain_context),
        "candidates": [
            {
                "candidate_id": row.candidate_id,
                "conflict_reason": row.conflict_reason,
                "original_commit_order": row.original_commit_order,
                "transport_kind": row.transport_kind,
                "domain_snapshot_index": row.domain_snapshot_index,
                "retry_round": row.retry_round,
            }
            for row in summary.candidates
        ],
    }


__all__ = [
    "build_deferred_retry_shadow_summary",
    "deferred_retry_shadow_metrics",
]
