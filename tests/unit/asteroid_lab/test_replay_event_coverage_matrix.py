"""Phase 9 pre-9B — ReplayEventType adapter coverage matrix."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.replay.replay_event_coverage import (
    DEFERRED_POST_9B,
    SUPPORTED_BY_9B_LAB_ADAPTER,
    replay_event_type_coverage_partitions,
)


def test_unified_replay_event_type_adapter_coverage_matrix_is_explicit() -> None:
    lab, post = replay_event_type_coverage_partitions()
    assert lab is SUPPORTED_BY_9B_LAB_ADAPTER
    assert post is DEFERRED_POST_9B
    assert not (lab & post)

    assert lab == frozenset(
        {
            ReplayEventType.DECODE_STARTED,
            ReplayEventType.DECODE_COMPLETED,
            ReplayEventType.RECONSTRUCTION_STARTED,
            ReplayEventType.RECONSTRUCTION_COMPLETED,
        }
    )
    assert len(post) == 0


def test_lab_adapter_members_are_valid_replay_event_types() -> None:
    for member in SUPPORTED_BY_9B_LAB_ADAPTER:
        assert member in ReplayEventType
