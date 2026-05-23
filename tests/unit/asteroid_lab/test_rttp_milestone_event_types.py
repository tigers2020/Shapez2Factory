"""RTTP milestone event_type normalization (3B-S-3)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.replay.event_types import (
    normalize_rttp_milestone_event_type,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType


def test_replay_event_type_enum_includes_rttp_snapshots() -> None:
    assert (
        ReplayEventType.RTTP_ROUTE_DOMAIN_SNAPSHOT.value
        == et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT
    )
    assert (
        ReplayEventType.RTTP_CANDIDATE_POOL_SNAPSHOT.value
        == et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT
    )
    assert (
        ReplayEventType.RTTP_GENOME_SELECTION_SNAPSHOT.value
        == et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT
    )
    assert (
        ReplayEventType.RTTP_COMMIT_DOMAIN_SNAPSHOT.value
        == et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT
    )


def test_normalize_legacy_v02_milestone_types_to_canonical() -> None:
    assert (
        normalize_rttp_milestone_event_type(et.EVENT_TYPE_ROUTING_PROBE_STARTED)
        == et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT
    )
    assert (
        normalize_rttp_milestone_event_type(et.EVENT_TYPE_CANDIDATE_GENERATED)
        == et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT
    )
    assert (
        normalize_rttp_milestone_event_type(et.EVENT_TYPE_GA_BEST_UPDATED)
        == et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT
    )
    assert (
        normalize_rttp_milestone_event_type(et.EVENT_TYPE_ROUTING_COMMITTED)
        == et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT
    )


def test_normalize_canonical_types_is_identity() -> None:
    for canonical in et.RTTP_MILESTONE_EVENT_TYPES:
        assert normalize_rttp_milestone_event_type(canonical) == canonical
