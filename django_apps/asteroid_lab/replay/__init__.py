"""Replay-first snapshot event contracts."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "DEFERRED_POST_9B",
    "LAB_EVENT_TYPE_TO_TIMELINE",
    "LabTimelineAdapterError",
    "MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME",
    "MAX_LAB_REPLAY_TIMELINE_FRAMES",
    "SNAPSHOT_EVENT_TYPES",
    "SUPPORTED_BY_9B_LAB_ADAPTER",
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
    "compose_replay_timeline",
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

_TIMELINE_SERIALIZATION = "django_apps.asteroid_lab.replay.timeline_serialization"

_EXPORT_MODULES = {
    "DEFERRED_POST_9B": "django_apps.asteroid_lab.replay.replay_event_coverage",
    "LAB_EVENT_TYPE_TO_TIMELINE": "django_apps.asteroid_lab.replay.lab_timeline_adapter",
    "LabTimelineAdapterError": "django_apps.asteroid_lab.replay.lab_timeline_adapter",
    "MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME": "django_apps.asteroid_lab.replay.replay_limits",
    "MAX_LAB_REPLAY_TIMELINE_FRAMES": "django_apps.asteroid_lab.replay.replay_limits",
    "SNAPSHOT_EVENT_TYPES": "django_apps.asteroid_lab.replay.event_types",
    "SUPPORTED_BY_9B_LAB_ADAPTER": "django_apps.asteroid_lab.replay.replay_event_coverage",
    "ReplayAnnotation": "django_apps.asteroid_lab.replay.timeline_dtos",
    "ReplayBBox": "django_apps.asteroid_lab.replay.timeline_dtos",
    "ReplayCell": "django_apps.asteroid_lab.replay.timeline_dtos",
    "ReplayCellDelta": "django_apps.asteroid_lab.replay.timeline_dtos",
    "ReplayEventType": "django_apps.asteroid_lab.replay.replay_enums",
    "ReplayMapView": "django_apps.asteroid_lab.replay.timeline_dtos",
    "ReplayOverlayCell": "django_apps.asteroid_lab.replay.timeline_dtos",
    "ReplayPhase": "django_apps.asteroid_lab.replay.replay_enums",
    "ReplayTimelineDeserializationError": _TIMELINE_SERIALIZATION,
    "ReplayTimelineFrame": "django_apps.asteroid_lab.replay.timeline_dtos",
    "assert_registered_event_type": "django_apps.asteroid_lab.replay.event_types",
    "compose_replay_timeline": "django_apps.asteroid_lab.replay.timeline_composer",
    "is_registered_event_type": "django_apps.asteroid_lab.replay.event_types",
    "lab_replay_row_to_timeline_frame": "django_apps.asteroid_lab.replay.lab_timeline_adapter",
    "lab_snapshot_event_to_timeline_frame": "django_apps.asteroid_lab.replay.lab_timeline_adapter",
    "parse_replay_event_type": _TIMELINE_SERIALIZATION,
    "parse_replay_phase": _TIMELINE_SERIALIZATION,
    "replay_bbox_from_json_dict": _TIMELINE_SERIALIZATION,
    "replay_bbox_to_json_dict": _TIMELINE_SERIALIZATION,
    "replay_map_view_from_json_dict": _TIMELINE_SERIALIZATION,
    "replay_map_view_is_renderable": "django_apps.asteroid_lab.replay.timeline_dtos",
    "replay_map_view_to_json_dict": _TIMELINE_SERIALIZATION,
    "replay_timeline_frame_from_json_dict": _TIMELINE_SERIALIZATION,
    "replay_timeline_frame_json_round_trip": _TIMELINE_SERIALIZATION,
    "replay_timeline_frame_to_json_dict": _TIMELINE_SERIALIZATION,
}


def __getattr__(name: str) -> Any:
    if name in _EXPORT_MODULES:
        module = import_module(_EXPORT_MODULES[name])
        return getattr(module, name)
    raise AttributeError(name)
