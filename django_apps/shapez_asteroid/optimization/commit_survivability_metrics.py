"""Post-commit survivability summary (Sequence 10B; diagnostics only, not GA input)."""

from __future__ import annotations

from collections import Counter

from django_apps.shapez_asteroid.optimization.dto import (
    CommitSurvivabilityMetrics,
    IncrementalCommitResult,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CommitConflictReason,
    PlacementCommitState,
)


def summarize_incremental_commit(res: IncrementalCommitResult) -> CommitSurvivabilityMetrics:
    """Derive deterministic commit survivability metrics from ``IncrementalCommitResult``."""

    rows = res.candidate_results
    attempts = len(rows)
    confirmed = res.confirmed_candidate_count
    rolled = res.rolled_back_candidate_count
    if confirmed + rolled != attempts:
        raise ValueError("incremental commit counts disagree with candidate_results length")
    ratio = (float(confirmed) / float(attempts)) if attempts > 0 else 0.0

    reason_counter: Counter[CommitConflictReason] = Counter()
    for r in rows:
        if r.commit_state is PlacementCommitState.ROLLED_BACK and r.conflict_reason is not None:
            reason_counter[r.conflict_reason] += 1

    rollback_pairs = tuple(sorted(reason_counter.items(), key=lambda z: (z[0].value, z[0].name)))

    n_probe_fail = sum(
        1 for r in rows if r.conflict_reason is CommitConflictReason.ROUTE_PROBE_FAILED
    )
    n_tk = sum(1 for r in rows if r.conflict_reason is CommitConflictReason.TRANSPORT_KIND_CONFLICT)

    return CommitSurvivabilityMetrics(
        commit_attempt_count=attempts,
        commit_confirmed_count=confirmed,
        commit_rolled_back_count=rolled,
        commit_success_ratio=ratio,
        rollback_reason_counts=rollback_pairs,
        route_probe_failed_count=n_probe_fail,
        transport_kind_conflict_count=n_tk,
    )


def commit_survivability_metrics_to_replay_metrics(
    m: CommitSurvivabilityMetrics,
    *,
    route_fragility_penalty: float = 0.0,
    shared_corridor_pressure_penalty: float = 0.0,
) -> dict[str, object]:
    """JSON-friendly flat metrics for ``OptimizationReplayFrame.metrics`` (output-only)."""

    rollback_json = {reason.value: count for reason, count in m.rollback_reason_counts}
    return {
        "commit_attempt_count": m.commit_attempt_count,
        "commit_confirmed_count": m.commit_confirmed_count,
        "commit_rolled_back_count": m.commit_rolled_back_count,
        "commit_success_ratio": m.commit_success_ratio,
        "rollback_reason_counts": rollback_json,
        "route_probe_failed_count": m.route_probe_failed_count,
        "transport_kind_conflict_count": m.transport_kind_conflict_count,
        "route_fragility_penalty": float(route_fragility_penalty),
        "shared_corridor_pressure_penalty": float(shared_corridor_pressure_penalty),
    }
