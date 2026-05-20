"""Explicit ReplayEventType adapter coverage (Phase 9B Lab / Phase 9F solver runtime)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType

# Lab adapter may emit only these timeline lifecycle wire values.
SUPPORTED_BY_9B_LAB_ADAPTER: frozenset[ReplayEventType] = frozenset(
    {
        ReplayEventType.DECODE_STARTED,
        ReplayEventType.DECODE_COMPLETED,
        ReplayEventType.RECONSTRUCTION_STARTED,
        ReplayEventType.RECONSTRUCTION_COMPLETED,
    }
)

# Solver runtime recorder (v0 pipeline — no evolutionary search loop).
SUPPORTED_BY_SOLVER_RUNTIME_RECORDER: frozenset[ReplayEventType] = frozenset(
    {
        ReplayEventType.OPTIMIZATION_INPUT_LOADED,
        ReplayEventType.CAPACITY_PLAN_CREATED,
        ReplayEventType.ROUTE_GOAL_GENERATED,
        ReplayEventType.CANDIDATE_POOL_COMPLETED,
        ReplayEventType.CANDIDATE_SELECTION_COMPLETED,
        ReplayEventType.ROUTE_COMMITTED,
        ReplayEventType.ROUTE_MATERIALIZED,
        ReplayEventType.VALIDATION_COMPLETED,
        ReplayEventType.VALIDATION_FAILED,
        ReplayEventType.RESULT_LAYOUT,
    }
)

# GA/evolution events not emitted by v0 pipeline (no evolutionary search loop).
DEFERRED_NO_EVOLUTION_V0: frozenset[ReplayEventType] = frozenset(
    {
        ReplayEventType.PATTERN_GENERATED,
        ReplayEventType.CANDIDATE_GENERATED,
        ReplayEventType.CANDIDATE_REJECTED,
        ReplayEventType.ROUTE_PROBE_SUCCEEDED,
        ReplayEventType.ROUTE_PROBE_FAILED,
        ReplayEventType.GENOME_GENERATED,
        ReplayEventType.GENOME_EVALUATED,
        ReplayEventType.GENERATION_COMPLETED,
        ReplayEventType.BEST_GENOME_SELECTED,
        ReplayEventType.ROUTE_COMMIT_ATTEMPTED,
        ReplayEventType.ROUTE_ROLLED_BACK,
    }
)

# Reserved for post-9B adapters (candidate/routing/ga lab events, etc.).
DEFERRED_POST_9B: frozenset[ReplayEventType] = frozenset()

_LAB_OUTPUT = SUPPORTED_BY_9B_LAB_ADAPTER
_POST = DEFERRED_POST_9B


def replay_event_type_coverage_partitions() -> tuple[
    frozenset[ReplayEventType],
    frozenset[ReplayEventType],
]:
    """Return (9B lab output, post-9B) coverage sets."""

    return (_LAB_OUTPUT, _POST)
