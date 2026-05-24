"""Deferred commit retry execution result (PR-3)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult


@dataclass(frozen=True, slots=True)
class DeferredRetryExecuteResult:
    merged_commit_result: CommitResult
    deferred_retry_rounds_executed: int
    deferred_retry_eligible_count: int
    deferred_retry_attempted_count: int
    deferred_retry_recovered_count: int
    deferred_retry_still_failed_count: int
    recovered_candidate_ids: tuple[str, ...]
    deferred_retry_failed_reason_counts: Mapping[str, int]


def deferred_retry_execute_metrics(result: DeferredRetryExecuteResult) -> dict[str, Any]:
    return {
        "deferred_retry_rounds_executed": result.deferred_retry_rounds_executed,
        "deferred_retry_eligible_count": result.deferred_retry_eligible_count,
        "deferred_retry_attempted_count": result.deferred_retry_attempted_count,
        "deferred_retry_recovered_count": result.deferred_retry_recovered_count,
        "deferred_retry_still_failed_count": result.deferred_retry_still_failed_count,
        "recovered_candidate_ids": list(result.recovered_candidate_ids),
        "deferred_retry_failed_reason_counts": dict(result.deferred_retry_failed_reason_counts),
    }


__all__ = [
    "DeferredRetryExecuteResult",
    "deferred_retry_execute_metrics",
]
