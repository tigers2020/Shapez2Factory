"""Merge Lab and runtime frames into one product replay timeline (Phase 9D)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.replay.replay_limits import MAX_LAB_REPLAY_TIMELINE_FRAMES
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayTimelineFrame

_TRUNCATION_REASON = "max_lab_replay_timeline_frames"

# Event types that must be retained when truncating (never dropped).
_REQUIRED_KEYFRAME_EVENTS: frozenset[ReplayEventType] = frozenset(
    {
        ReplayEventType.RECONSTRUCTION_COMPLETED,
        ReplayEventType.RESULT_LAYOUT,
    }
)


def _retain_keyframes_and_tail(
    frames: list[ReplayTimelineFrame],
    cap: int,
) -> tuple[list[ReplayTimelineFrame], int]:
    """Retain required keyframes + tail frames within *cap* slots.

    Strategy:
    1. Collect required keyframes (RECONSTRUCTION_COMPLETED, RESULT_LAYOUT) by
       taking the *first* occurrence of RECONSTRUCTION_COMPLETED and the *last*
       occurrence of RESULT_LAYOUT.
    2. Fill remaining slots with tail frames (most recent non-keyframe frames).
    3. Merge and sort by original list index to preserve temporal order.

    Returns ``(retained_frames, dropped_count)``.
    """
    if len(frames) <= cap:
        return frames, 0

    pinned_indices: set[int] = set()
    first_recon = next(
        (
            i
            for i, f in enumerate(frames)
            if f.event_type == ReplayEventType.RECONSTRUCTION_COMPLETED
        ),
        None,
    )
    if first_recon is not None:
        pinned_indices.add(first_recon)
    last_result = next(
        (
            i
            for i, f in reversed(list(enumerate(frames)))
            if f.event_type == ReplayEventType.RESULT_LAYOUT
        ),
        None,
    )
    if last_result is not None:
        pinned_indices.add(last_result)

    remaining_slots = cap - len(pinned_indices)
    if remaining_slots < 0:
        remaining_slots = 0

    tail_indices: list[int] = []
    for i in reversed(range(len(frames))):
        if i in pinned_indices:
            continue
        if len(tail_indices) >= remaining_slots:
            break
        tail_indices.append(i)

    selected = sorted(pinned_indices | set(tail_indices))
    retained = [frames[i] for i in selected]
    dropped = len(frames) - len(retained)
    return retained, dropped


def compose_replay_timeline(
    *,
    lab_frames: Sequence[ReplayTimelineFrame],
    max_frames: int = MAX_LAB_REPLAY_TIMELINE_FRAMES,
) -> tuple[ReplayTimelineFrame, ...]:
    """Assign global ``frame_index`` 0..n-1; truncate when over *max_frames*.

    When the count exceeds *max_frames*, required keyframes
    (RECONSTRUCTION_COMPLETED, RESULT_LAYOUT) are always retained; remaining
    slots are filled with tail frames in temporal order.
    """

    combined = list(lab_frames)
    original_count = len(combined)
    cap = max(1, int(max_frames))
    truncated = original_count > cap
    if truncated:
        combined, dropped_frame_count = _retain_keyframes_and_tail(combined, cap)
    else:
        dropped_frame_count = 0

    out: list[ReplayTimelineFrame] = []
    for new_index, frame in enumerate(combined):
        inspector = dict(frame.inspector)
        if "source_frame_index" not in inspector:
            inspector["source_frame_index"] = int(frame.frame_index)
        metrics = dict(frame.metrics)
        if truncated and new_index == len(combined) - 1:
            metrics["replay_truncated"] = True
            metrics["truncation_reason"] = _TRUNCATION_REASON
            if dropped_frame_count > 0:
                metrics["dropped_frame_count"] = dropped_frame_count
        out.append(
            replace(
                frame,
                frame_index=new_index,
                inspector=inspector,
                metrics=metrics,
            )
        )
    return tuple(out)
