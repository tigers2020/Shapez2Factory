"""Lab replay lazy-load handle DTO (Sequence 13C transport contract)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from django.conf import settings

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


def _lab_replay_fetch_url(*, project_slug: str, solver_run_id: int) -> str:
    return f"/asteroid-miner-layout/p/{project_slug}/solver-runs/{int(solver_run_id)}/lab-replay/"


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
        fetch_url = _lab_replay_fetch_url(
            project_slug=str(project_slug),
            solver_run_id=int(solver_run_id),
        )
    return LabReplayLazyHandle(
        mode=mode,
        frame_count=count,
        preview_frame_index=preview_index,
        preview_frame=preview,
        fetch_url=fetch_url,
        replay_payload_version=LAB_REPLAY_PAYLOAD_VERSION,
    )


__all__ = [
    "LAB_REPLAY_PAYLOAD_VERSION",
    "LabReplayLazyHandle",
    "LabReplayPayloadMode",
    "build_lab_replay_lazy_handle",
    "lab_replay_payload_mode",
]
