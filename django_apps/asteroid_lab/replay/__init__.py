"""Replay-first snapshot event contracts (event type registry)."""

from django_apps.asteroid_lab.replay.event_types import (
    SNAPSHOT_EVENT_TYPES,
    assert_registered_event_type,
    is_registered_event_type,
)
from django_apps.asteroid_lab.replay.lab_timeline_adapter import (
    LAB_EVENT_TYPE_TO_TIMELINE,
    LabTimelineAdapterError,
    lab_replay_row_to_timeline_frame,
    lab_snapshot_event_to_timeline_frame,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.replay_event_coverage import (
    DEFERRED_POST_9B,
    SUPPORTED_BY_9B_LAB_ADAPTER,
)
from django_apps.asteroid_lab.replay.replay_limits import (
    MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME,
    MAX_LAB_REPLAY_TIMELINE_FRAMES,
)
from django_apps.asteroid_lab.replay.timeline_composer import compose_replay_timeline
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayAnnotation,
    ReplayBBox,
    ReplayCell,
    ReplayCellDelta,
    ReplayMapView,
    ReplayOverlayCell,
    ReplayTimelineFrame,
    replay_map_view_is_renderable,
)
from django_apps.asteroid_lab.replay.timeline_serialization import (
    ReplayTimelineDeserializationError,
    parse_replay_event_type,
    parse_replay_phase,
    replay_bbox_from_json_dict,
    replay_bbox_to_json_dict,
    replay_map_view_from_json_dict,
    replay_map_view_to_json_dict,
    replay_timeline_frame_from_json_dict,
    replay_timeline_frame_json_round_trip,
    replay_timeline_frame_to_json_dict,
)

__all__ = [
    "DEFERRED_POST_9B",
    "LAB_EVENT_TYPE_TO_TIMELINE",
    "LabTimelineAdapterError",
    "MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME",
    "MAX_LAB_REPLAY_TIMELINE_FRAMES",
    "SNAPSHOT_EVENT_TYPES",
    "SUPPORTED_BY_9B_LAB_ADAPTER",
    "compose_replay_timeline",
    "ReplayAnnotation",
    "ReplayBBox",
    "ReplayCell",
    "ReplayCellDelta",
    "ReplayEventType",
    "ReplayMapView",
    "ReplayOverlayCell",
    "ReplayPhase",
    "ReplayTimelineDeserializationError",
    "ReplayTimelineFrame",
    "assert_registered_event_type",
    "is_registered_event_type",
    "lab_replay_row_to_timeline_frame",
    "lab_snapshot_event_to_timeline_frame",
    "parse_replay_event_type",
    "parse_replay_phase",
    "replay_bbox_from_json_dict",
    "replay_bbox_to_json_dict",
    "replay_map_view_from_json_dict",
    "replay_map_view_is_renderable",
    "replay_map_view_to_json_dict",
    "replay_timeline_frame_from_json_dict",
    "replay_timeline_frame_json_round_trip",
    "replay_timeline_frame_to_json_dict",
]
