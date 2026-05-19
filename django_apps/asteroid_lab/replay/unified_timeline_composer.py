"""Merge Lab + optimization unified frames into one global timeline (Phase 9D)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from django_apps.asteroid_lab.replay.replay_limits import MAX_UNIFIED_LAB_REPLAY_FRAMES
from django_apps.asteroid_lab.replay.unified_dtos import UnifiedReplayFrame

_TRUNCATION_REASON = "max_unified_replay_frames"


def compose_unified_timeline(
    *,
    lab_frames: Sequence[UnifiedReplayFrame],
    optimization_frames: Sequence[UnifiedReplayFrame],
    max_frames: int = MAX_UNIFIED_LAB_REPLAY_FRAMES,
) -> tuple[UnifiedReplayFrame, ...]:
    """Concatenate lab then optimization frames; assign global ``frame_index`` 0..n-1."""

    combined = list(lab_frames) + list(optimization_frames)
    cap = max(1, int(max_frames))
    truncated = len(combined) > cap
    if truncated:
        combined = combined[:cap]

    out: list[UnifiedReplayFrame] = []
    for new_index, frame in enumerate(combined):
        inspector = dict(frame.inspector)
        if "source_frame_index" not in inspector:
            inspector["source_frame_index"] = int(frame.frame_index)
        metrics = dict(frame.metrics)
        if truncated and new_index == len(combined) - 1:
            metrics["replay_truncated"] = True
            metrics["truncation_reason"] = _TRUNCATION_REASON
        out.append(
            replace(
                frame,
                frame_index=new_index,
                inspector=inspector,
                metrics=metrics,
            )
        )
    return tuple(out)
