"""Explicit ReplayEventType adapter coverage (Phase 9B Lab)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType

# Lab adapter may emit only these unified lifecycle wire values.
SUPPORTED_BY_9B_LAB_ADAPTER: frozenset[ReplayEventType] = frozenset(
    {
        ReplayEventType.DECODE_STARTED,
        ReplayEventType.DECODE_COMPLETED,
        ReplayEventType.RECONSTRUCTION_STARTED,
        ReplayEventType.RECONSTRUCTION_COMPLETED,
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
