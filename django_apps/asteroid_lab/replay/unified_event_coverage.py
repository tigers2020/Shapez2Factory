"""Explicit ReplayEventType adapter coverage (Phase 9B / 9C)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType

# 9B Lab adapter may emit only these unified lifecycle wire values.
SUPPORTED_BY_9B_LAB_ADAPTER: frozenset[ReplayEventType] = frozenset(
    {
        ReplayEventType.DECODE_STARTED,
        ReplayEventType.DECODE_COMPLETED,
        ReplayEventType.RECONSTRUCTION_STARTED,
        ReplayEventType.RECONSTRUCTION_COMPLETED,
    }
)

# 9C optimization → unified map_view adapter.
SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER: frozenset[ReplayEventType] = frozenset(
    {
        ReplayEventType.OPTIMIZATION_INPUT_LOADED,
        ReplayEventType.CAPACITY_PLAN_CREATED,
        ReplayEventType.ROUTE_GOAL_GENERATED,
        ReplayEventType.PATTERN_GENERATED,
        ReplayEventType.CANDIDATE_GENERATED,
        ReplayEventType.CANDIDATE_REJECTED,
        ReplayEventType.ROUTE_PROBE_SUCCEEDED,
        ReplayEventType.ROUTE_PROBE_FAILED,
        ReplayEventType.CANDIDATE_POOL_COMPLETED,
        ReplayEventType.CANDIDATE_SELECTION_COMPLETED,
        ReplayEventType.GENOME_GENERATED,
        ReplayEventType.GENOME_EVALUATED,
        ReplayEventType.GENERATION_COMPLETED,
        ReplayEventType.BEST_GENOME_SELECTED,
        ReplayEventType.ROUTE_COMMIT_ATTEMPTED,
        ReplayEventType.ROUTE_COMMITTED,
        ReplayEventType.ROUTE_ROLLED_BACK,
        ReplayEventType.ROUTE_MATERIALIZED,
        ReplayEventType.VALIDATION_COMPLETED,
        ReplayEventType.VALIDATION_FAILED,
        ReplayEventType.RESULT_LAYOUT,
    }
)

# Deprecated alias (pre-9C name); use SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER.
DEFERRED_TO_9C_OPTIMIZATION_ADAPTER = SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER

# Reserved for post-9B / post-9C adapters (candidate/routing/ga lab events, etc.).
DEFERRED_POST_9B: frozenset[ReplayEventType] = frozenset()

_LAB_OUTPUT = SUPPORTED_BY_9B_LAB_ADAPTER
_OPT = SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER
_POST = DEFERRED_POST_9B


def replay_event_type_coverage_partitions() -> tuple[
    frozenset[ReplayEventType],
    frozenset[ReplayEventType],
    frozenset[ReplayEventType],
]:
    """Return (9B lab output, 9C optimization, post-9B) coverage sets."""

    return (_LAB_OUTPUT, _OPT, _POST)
