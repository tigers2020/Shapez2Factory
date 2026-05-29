"""Lab replay lazy-load handle DTO (Sequence 13C transport contract)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from django.conf import settings
from django.urls import reverse

LAB_REPLAY_PAYLOAD_VERSION = 1
LabReplayPayloadMode = Literal["inline", "lazy"]


@dataclass(frozen=True)
class LabReplayLazyHandle:
    mode: LabReplayPayloadMode
    frame_count: int
    preview_frame_index: int
    preview_frame: Mapping[str, Any] | None
    fetch_url: str | None
    replay_payload_version: int


def lab_replay_payload_mode() -> LabReplayPayloadMode:
    raw = str(getattr(settings, "ASTEROID_LAB_REPLAY_PAYLOAD_MODE", "lazy")).strip().lower()
    return "inline" if raw == "inline" else "lazy"


def build_lab_replay_lazy_handle(
    *,
    mode: LabReplayPayloadMode,
    frames: list[dict[str, Any]],
    project_slug: str,
    solver_run_id: int | None,
) -> LabReplayLazyHandle:
    count = len(frames)
    preview_index = max(0, count - 1) if count else 0
    preview = dict(frames[preview_index]) if count else None
    fetch_url: str | None = None
    if mode == "lazy" and solver_run_id is not None and project_slug:
        fetch_url = reverse(
            "web:asteroid-miner-layout-project-solver-run-lab-replay",
            kwargs={"slug": str(project_slug), "run_id": int(solver_run_id)},
        )
    return LabReplayLazyHandle(
        mode=mode,
        frame_count=count,
        preview_frame_index=preview_index,
        preview_frame=preview,
        fetch_url=fetch_url,
        replay_payload_version=LAB_REPLAY_PAYLOAD_VERSION,
    )


def lab_replay_manifest_json_dict(
    *,
    handle: LabReplayLazyHandle,
    replay_track_metrics: dict[str, Any],
) -> dict[str, Any]:
    preview = handle.preview_frame
    return {
        "mode": handle.mode,
        "frame_count": int(handle.frame_count),
        "preview_frame_index": int(handle.preview_frame_index),
        "preview_frame": dict(preview) if preview is not None else None,
        "fetch_url": handle.fetch_url,
        "replay_payload_version": int(handle.replay_payload_version),
        "replay_track_metrics": dict(replay_track_metrics),
    }


__all__ = [
    "LAB_REPLAY_PAYLOAD_VERSION",
    "LabReplayLazyHandle",
    "LabReplayPayloadMode",
    "build_lab_replay_lazy_handle",
    "lab_replay_manifest_json_dict",
    "lab_replay_payload_mode",
]
