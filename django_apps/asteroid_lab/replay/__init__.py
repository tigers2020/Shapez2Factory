"""Replay-first snapshot event contracts (event type registry)."""

from django_apps.asteroid_lab.replay.event_types import (
    SNAPSHOT_EVENT_TYPES,
    assert_registered_event_type,
    is_registered_event_type,
)
from django_apps.asteroid_lab.replay.lab_unified_adapter import (
    LAB_EVENT_TYPE_TO_UNIFIED,
    LabUnifiedAdapterError,
    lab_replay_row_to_unified,
    lab_snapshot_event_to_unified,
)
from django_apps.asteroid_lab.replay.replay_limits import (
    MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME,
    MAX_OPTIMIZATION_REPLAY_FRAMES,
    MAX_UNIFIED_LAB_REPLAY_CELLS_PER_FRAME,
    MAX_UNIFIED_LAB_REPLAY_FRAMES,
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
from django_apps.asteroid_lab.replay.unified_event_coverage import (
    DEFERRED_POST_9B,
    DEFERRED_TO_9C_OPTIMIZATION_ADAPTER,
    SUPPORTED_BY_9B_LAB_ADAPTER,
    SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER,
)
from django_apps.asteroid_lab.replay.unified_timeline_composer import compose_unified_timeline
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
    "DEFERRED_POST_9B",
    "DEFERRED_TO_9C_OPTIMIZATION_ADAPTER",
    "LAB_EVENT_TYPE_TO_UNIFIED",
    "LabUnifiedAdapterError",
    "MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME",
    "MAX_OPTIMIZATION_REPLAY_FRAMES",
    "MAX_UNIFIED_LAB_REPLAY_CELLS_PER_FRAME",
    "MAX_UNIFIED_LAB_REPLAY_FRAMES",
    "SNAPSHOT_EVENT_TYPES",
    "SUPPORTED_BY_9B_LAB_ADAPTER",
    "SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER",
    "compose_unified_timeline",
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
    "lab_replay_row_to_unified",
    "lab_snapshot_event_to_unified",
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
