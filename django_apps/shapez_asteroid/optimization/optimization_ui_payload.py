"""Sequence 9 — optimization replay track as JSON-safe Lab payload (output-only).

This module does not wire into Django views or templates by itself. Callers that
build Lab page context (e.g. ``django_apps.web.services.asteroid_lab_page_context``)
may merge :func:`merge_optimization_track_into_lab_payload` once an optimization
runner supplies
:class:`~django_apps.shapez_asteroid.optimization.dto.OptimizationReplayFrame`
tuples from
:class:`~django_apps.shapez_asteroid.optimization.optimization_replay.OptimizationReplayRecorder`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypedDict

from django_apps.shapez_asteroid.optimization.dto import OptimizationReplayFrame
from django_apps.shapez_asteroid.optimization.optimization_replay import (
    optimization_replay_frame_to_json_dict,
)

TRACK_ID = "optimization"
TRACK_LABEL = "Optimization"

# Lab / API flat field (Option B — smallest change vs existing ``lab_*`` keys).
OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY = "optimization_replay"


class OptimizationReplayTrackPayload(TypedDict):
    """v0 track envelope merged under :data:`OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY`."""

    track_id: str
    track_label: str
    frame_count: int
    frames: list[dict[str, Any]]
    metrics: dict[str, Any]


def _event_type_counts_sorted(frames: Sequence[OptimizationReplayFrame]) -> dict[str, int]:
    raw: dict[str, int] = {}
    for f in frames:
        key = f.event_type.value
        raw[key] = raw.get(key, 0) + 1
    return dict(sorted(raw.items()))


def _aggregate_replay_truncated(frames: Sequence[OptimizationReplayFrame]) -> bool:
    return any(bool(f.metrics.get("replay_truncated")) for f in frames)


def empty_optimization_replay_track_payload() -> dict[str, object]:
    """Empty optimization track (no frames, no truncation)."""

    return {
        "track_id": TRACK_ID,
        "track_label": TRACK_LABEL,
        "frame_count": 0,
        "frames": [],
        "metrics": {
            "frame_count": 0,
            "event_type_counts": {},
            "replay_truncated": False,
        },
    }


def build_optimization_replay_track_payload(
    frames: Sequence[OptimizationReplayFrame],
) -> dict[str, object]:
    """Serialize frames via :func:`optimization_replay_frame_to_json_dict` only (read-only)."""

    if not frames:
        return empty_optimization_replay_track_payload()

    serialized = [optimization_replay_frame_to_json_dict(f) for f in frames]
    return {
        "track_id": TRACK_ID,
        "track_label": TRACK_LABEL,
        "frame_count": len(serialized),
        "frames": serialized,
        "metrics": {
            "frame_count": len(serialized),
            "event_type_counts": _event_type_counts_sorted(frames),
            "replay_truncated": _aggregate_replay_truncated(frames),
        },
    }


def merge_optimization_track_into_lab_payload(
    base_payload: Mapping[str, object],
    frames: Sequence[OptimizationReplayFrame],
) -> dict[str, object]:
    """Shallow-copy ``base_payload`` and attach the optimization track (does not mutate input)."""

    merged: dict[str, object] = dict(base_payload)
    merged[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] = build_optimization_replay_track_payload(frames)
    return merged
