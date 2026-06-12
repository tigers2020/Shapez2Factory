"""Replay timeline persistence.

**Architectural rule:** ``ReplayFrame`` / ``ReplayTrack`` / ``UIPlaybackSession`` rows are
**never** solver algorithm input. They exist for UI playback, scrubber state, and inspection
only. The solver engine must consume pure in-memory DTOs with **zero** reads of these tables as
inputs to optimization logic.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import Max

from django_apps.asteroid_lab.models import (
    ReplayFrame,
    ReplayTrack,
    UIPlaybackSession,
)
from django_apps.asteroid_lab.services.dto import (
    PlaybackPatchDTO,
    PlaybackSessionDTO,
    ReplayFrameDTO,
    ReplayFrameRowDTO,
    ReplayTrackPayloadDTO,
)


def _next_frame_index(track_id: int) -> int:
    agg = ReplayFrame.objects.filter(replay_track_id=track_id).aggregate(m=Max("frame_index"))
    max_idx = agg["m"]
    if max_idx is None:
        return 0
    return int(max_idx) + 1


def next_replay_frame_index(track_id: int) -> int:
    """Next ``frame_index`` that :func:`append_replay_frame` would assign (read-only ordering).

    Used by replay recorders for bookkeeping only — **not** solver algorithm input.
    """

    if not ReplayTrack.objects.filter(pk=track_id).exists():
        msg = f"ReplayTrack id={track_id} does not exist"
        raise ValueError(msg)
    return _next_frame_index(track_id)


def _frame_row(m: ReplayFrame) -> ReplayFrameRowDTO:
    return ReplayFrameRowDTO(
        id=m.id,
        frame_index=m.frame_index,
        frame_key=m.frame_key,
        phase=m.phase,
        title=m.title,
        description=m.description,
        frame_payload=dict(m.frame_payload or {}),
        cell_overlay_json=dict(m.cell_overlay_json or {}),
        metric_snapshot_json=dict(m.metric_snapshot_json or {}),
        is_placeholder=m.is_placeholder,
        is_keyframe=m.is_keyframe,
    )


def _session_dto(s: UIPlaybackSession) -> PlaybackSessionDTO:
    return PlaybackSessionDTO(
        replay_track_id=s.replay_track_id,
        current_frame_index=s.current_frame_index,
        is_playing=s.is_playing,
        playback_speed_ms=s.playback_speed_ms,
        selected_layer=s.selected_layer,
        selected_candidate_id=s.selected_candidate_id,
        selected_bundle_id=s.selected_bundle_id,
        ui_state_json=dict(s.ui_state_json or {}),
    )


@transaction.atomic
def append_replay_frame(track_id: int, frame: ReplayFrameDTO) -> ReplayFrameRowDTO:
    """Append one ``ReplayFrame`` with strictly monotonic ``frame_index``.

    Stored replay rows are **UI timeline / inspection only** — never feed them back as solver
    algorithm input.
    """

    track = ReplayTrack.objects.select_for_update().filter(pk=track_id).first()
    if track is None:
        msg = f"ReplayTrack id={track_id} does not exist"
        raise ValueError(msg)

    expected = _next_frame_index(track_id)
    idx = expected if frame.frame_index is None else int(frame.frame_index)
    if idx != expected:
        msg = f"frame_index must be {expected} (monotonic); got {idx}"
        raise ValueError(msg)

    row = ReplayFrame.objects.create(
        replay_track=track,
        frame_index=idx,
        frame_key=frame.frame_key,
        phase=frame.phase,
        title=frame.title,
        description=frame.description,
        frame_payload=dict(frame.frame_payload or {}),
        cell_overlay_json=dict(frame.cell_overlay_json or {}),
        metric_snapshot_json=dict(frame.metric_snapshot_json or {}),
        is_placeholder=frame.is_placeholder,
        is_keyframe=frame.is_keyframe,
    )
    return _frame_row(row)


def get_replay_track_payload(track_id: int) -> ReplayTrackPayloadDTO:
    """Return ordered frames including ``metric_snapshot_json`` overlays (UI only)."""

    track = ReplayTrack.objects.filter(pk=track_id).first()
    if track is None:
        msg = f"ReplayTrack id={track_id} does not exist"
        raise ValueError(msg)

    frames_qs = ReplayFrame.objects.filter(replay_track_id=track_id).order_by("frame_index", "id")
    frames = tuple(_frame_row(f) for f in frames_qs)
    return ReplayTrackPayloadDTO(
        track_id=track.id,
        project_id=track.project_id,
        solver_run_id=track.solver_run_id,
        track_key=track.track_key,
        title=track.title,
        frames=frames,
    )


@transaction.atomic
def update_playback_session(track_id: int, patch: PlaybackPatchDTO) -> PlaybackSessionDTO:
    """Upsert ``UIPlaybackSession`` for the track (transport UI state only).

    ``UIPlaybackSession`` is ``OneToOneField`` to ``ReplayTrack`` — at most one session row per
    track. Repeated calls with the same ``track_id`` update the same row (idempotent upsert).
    """

    if not ReplayTrack.objects.filter(pk=track_id).exists():
        msg = f"ReplayTrack id={track_id} does not exist"
        raise ValueError(msg)

    session, _created = UIPlaybackSession.objects.select_for_update().get_or_create(
        replay_track_id=track_id,
    )
    updates: list[str] = []
    if patch.current_frame_index is not None:
        session.current_frame_index = patch.current_frame_index
        updates.append("current_frame_index")
    if patch.is_playing is not None:
        session.is_playing = patch.is_playing
        updates.append("is_playing")
    if patch.playback_speed_ms is not None:
        session.playback_speed_ms = patch.playback_speed_ms
        updates.append("playback_speed_ms")
    if patch.selected_layer is not None:
        session.selected_layer = patch.selected_layer
        updates.append("selected_layer")
    if patch.selected_candidate_id is not None:
        session.selected_candidate_id = patch.selected_candidate_id
        updates.append("selected_candidate_id")
    if patch.selected_bundle_id is not None:
        session.selected_bundle_id = patch.selected_bundle_id
        updates.append("selected_bundle_id")
    if patch.ui_state_json is not None:
        merged: dict[str, object] = {**dict(session.ui_state_json or {}), **patch.ui_state_json}
        session.ui_state_json = merged
        updates.append("ui_state_json")

    if updates:
        session.save(update_fields=updates + ["updated_at"])
    else:
        session.save(update_fields=["updated_at"])

    session.refresh_from_db()
    return _session_dto(session)
