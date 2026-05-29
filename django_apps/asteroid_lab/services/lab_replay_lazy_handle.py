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


def _lab_replay_fetch_url(
    *,
    mode: LabReplayPayloadMode,
    project_slug: str,
    solver_run_id: int | None,
    frame_count: int,
) -> str | None:
    if mode != "lazy" or solver_run_id is None or not project_slug or frame_count <= 0:
        return None
    return reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": str(project_slug), "run_id": int(solver_run_id)},
    )


def _replay_payload_version_from_summary(manifest_summary: Mapping[str, Any]) -> int:
    raw = manifest_summary.get("replay_payload_version", LAB_REPLAY_PAYLOAD_VERSION)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return LAB_REPLAY_PAYLOAD_VERSION


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
    fetch_url = _lab_replay_fetch_url(
        mode=mode,
        project_slug=project_slug,
        solver_run_id=solver_run_id,
        frame_count=count,
    )
    return LabReplayLazyHandle(
        mode=mode,
        frame_count=count,
        preview_frame_index=preview_index,
        preview_frame=preview,
        fetch_url=fetch_url,
        replay_payload_version=LAB_REPLAY_PAYLOAD_VERSION,
    )


def build_lab_replay_lazy_handle_from_summary(
    *,
    project_slug: str,
    solver_run_id: int | None,
    manifest_summary: Mapping[str, Any],
) -> LabReplayLazyHandle:
    """Build lazy handle from persisted manifest summary (no composed frame list)."""

    mode = lab_replay_payload_mode()
    try:
        count = int(manifest_summary.get("frame_count", 0))
    except (TypeError, ValueError):
        count = 0
    try:
        preview_index = int(manifest_summary.get("preview_frame_index", 0))
    except (TypeError, ValueError):
        preview_index = 0
    preview_raw = manifest_summary.get("preview_frame")
    preview = dict(preview_raw) if isinstance(preview_raw, dict) else None
    fetch_url = _lab_replay_fetch_url(
        mode=mode,
        project_slug=project_slug,
        solver_run_id=solver_run_id,
        frame_count=count,
    )
    return LabReplayLazyHandle(
        mode=mode,
        frame_count=count,
        preview_frame_index=preview_index,
        preview_frame=preview,
        fetch_url=fetch_url,
        replay_payload_version=_replay_payload_version_from_summary(manifest_summary),
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
    "build_lab_replay_lazy_handle_from_summary",
    "lab_replay_manifest_json_dict",
    "lab_replay_payload_mode",
]
