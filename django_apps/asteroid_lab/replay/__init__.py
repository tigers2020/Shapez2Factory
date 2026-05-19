"""Replay-first snapshot event contracts (event type registry)."""

from django_apps.asteroid_lab.replay.event_types import (
    SNAPSHOT_EVENT_TYPES,
    assert_registered_event_type,
    is_registered_event_type,
)
from django_apps.asteroid_lab.replay.unified_dtos import (
    ReplayAnnotation,
    ReplayBBox,
    ReplayCell,
    ReplayCellDelta,
    ReplayMapView,
    ReplayOverlayCell,
    UnifiedReplayFrame,
    replay_map_view_is_renderable,
)
from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.unified_serialization import (
    UnifiedReplayDeserializationError,
    parse_replay_event_type,
    parse_replay_phase,
    replay_bbox_from_json_dict,
    replay_bbox_to_json_dict,
    replay_map_view_from_json_dict,
    replay_map_view_to_json_dict,
    unified_replay_frame_from_json_dict,
    unified_replay_frame_json_round_trip,
    unified_replay_frame_to_json_dict,
)

__all__ = [
    "SNAPSHOT_EVENT_TYPES",
    "ReplayAnnotation",
    "ReplayBBox",
    "ReplayCell",
    "ReplayCellDelta",
    "ReplayEventType",
    "ReplayMapView",
    "ReplayOverlayCell",
    "ReplayPhase",
    "UnifiedReplayDeserializationError",
    "UnifiedReplayFrame",
    "assert_registered_event_type",
    "is_registered_event_type",
    "parse_replay_event_type",
    "parse_replay_phase",
    "replay_bbox_from_json_dict",
    "replay_bbox_to_json_dict",
    "replay_map_view_from_json_dict",
    "replay_map_view_is_renderable",
    "replay_map_view_to_json_dict",
    "unified_replay_frame_from_json_dict",
    "unified_replay_frame_json_round_trip",
    "unified_replay_frame_to_json_dict",
]
