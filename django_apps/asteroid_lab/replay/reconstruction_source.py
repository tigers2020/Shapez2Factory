"""Lab timeline helpers for reconstruction-complete source frames (replay package)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.services.lab_timeline_rim_enrichment import frame_has_renderable_map


def find_reconstruction_complete_source_frame(
    frames: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Last renderable ``reconstruction.completed`` frame (L1 map base for runtime append)."""

    for frame in reversed(frames):
        if frame.get("event_type") != ReplayEventType.RECONSTRUCTION_COMPLETED.value:
            continue
        if frame_has_renderable_map(frame):
            return frame
    return None


__all__ = ["find_reconstruction_complete_source_frame"]
