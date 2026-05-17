"""Default template context for the asteroid mining lab page (no demo payload)."""

from __future__ import annotations

from typing import Any, cast

from django.db.models import Count, Prefetch

from django_apps.asteroid_lab.models import ReplayFrame, ReplayTrack
from django_apps.shapez_asteroid.optimization.optimization_ui_payload import (
    OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY,
    empty_optimization_replay_track_payload,
)

GRID_W, GRID_H = 23, 15
CELL_COUNT = GRID_W * GRID_H

LAB_CELL_NEUTRAL = (
    "lab-cell relative h-5 w-5 shrink-0 overflow-visible rounded-[5px] border "
    "bg-slate-950 border-slate-900"
)


def _neutral_overlay_matrix() -> list[list[str]]:
    row = [LAB_CELL_NEUTRAL, LAB_CELL_NEUTRAL, LAB_CELL_NEUTRAL]
    return [list(row) for _ in range(CELL_COUNT)]


def _single_cell_overlay_matrix() -> list[list[str]]:
    """One SSR cell when server replay exists; Lab JS rebuilds the real grid."""

    row = [LAB_CELL_NEUTRAL, LAB_CELL_NEUTRAL, LAB_CELL_NEUTRAL]
    return [list(row)]


def get_latest_lab_replay_track() -> ReplayTrack | None:
    """Latest :class:`ReplayTrack` that has at least one frame (display-only read)."""

    ordered_frames = ReplayFrame.objects.order_by("frame_index", "id")
    return cast(
        ReplayTrack | None,
        ReplayTrack.objects.annotate(_frame_count=Count("frames"))
        .filter(_frame_count__gt=0)
        .order_by("-created_at", "-id")
        .prefetch_related(Prefetch("frames", queryset=ordered_frames))
        .first(),
    )


def get_latest_lab_replay_track_for_project(project_id: int) -> ReplayTrack | None:
    """Latest replay track (with frames) for a single persisted AsteroidProject."""

    ordered_frames = ReplayFrame.objects.order_by("frame_index", "id")
    return cast(
        ReplayTrack | None,
        ReplayTrack.objects.filter(project_id=int(project_id))
        .annotate(_frame_count=Count("frames"))
        .filter(_frame_count__gt=0)
        .order_by("-created_at", "-id")
        .prefetch_related(Prefetch("frames", queryset=ordered_frames))
        .first(),
    )


def serialize_replay_frame(frame: ReplayFrame) -> dict[str, Any]:
    """JSON-serializable replay frame for the Lab UI (output artifact only)."""

    payload: dict[str, Any] = dict(frame.frame_payload or {})
    event_type = str(payload.get("event_type") or "")
    full_map = payload.get("full_map")
    if not isinstance(full_map, list) or len(full_map) == 0:
        co = dict(frame.cell_overlay_json or {})
        cells = co.get("cells")
        full_map = list(cells) if isinstance(cells, list) else []
    diff = payload.get("diff")
    if not isinstance(diff, dict):
        diff = {}
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        summary = dict(frame.metric_snapshot_json or {})
    return {
        "id": int(frame.pk),
        "frame_index": int(frame.frame_index),
        "frame_id": str(frame.frame_key),
        "frame_key": str(frame.frame_key),
        "phase": str(frame.phase),
        "event_type": event_type,
        "title": str(frame.title),
        "description": str(frame.description or ""),
        "is_placeholder": bool(frame.is_placeholder),
        "is_keyframe": bool(frame.is_keyframe),
        "frame_payload": payload,
        "cell_overlay_json": dict(frame.cell_overlay_json or {}),
        "metric_snapshot_json": dict(frame.metric_snapshot_json or {}),
        "full_map": full_map,
        "diff": diff,
        "summary": summary,
    }


def build_lab_replay_payload(track: ReplayTrack) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Ordered serialized frames and the first frame dict for initial paint."""

    frames_iter = sorted(track.frames.all(), key=lambda f: (int(f.frame_index), int(f.pk)))
    serialized = [serialize_replay_frame(f) for f in frames_iter]
    initial = serialized[0] if serialized else {}
    return serialized, initial


def neutral_lab_context() -> dict[str, Any]:
    matrix = _neutral_overlay_matrix()
    initial_frame = 0
    total_frames = 0
    initial_classes = [row[0] for row in matrix]
    return {
        "total_frames": total_frames,
        "initial_frame": initial_frame,
        "initial_replay_phase": "—",
        "lab_cell_initial_classes": initial_classes,
        "lab_cell_overlay_matrix": matrix,
        "runs": [],
        "extractor_rules": [],
        "topology_rules": [],
        "stages_display": [],
        "lab_replay_track_id": None,
        "lab_replay_track_key": None,
        "lab_replay_frames_json": [],
        "lab_initial_replay_frame_json": {},
        "has_replay_frames": False,
        "lab_ui_initial": {
            "frame": initial_frame,
            "totalFrames": total_frames,
            "blueprintCode": "",
            "hasReplayFrames": False,
            "replayTrackId": None,
            "replayTrackKey": None,
        },
        OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY: empty_optimization_replay_track_payload(),
    }


def lab_page_context(*, project_id: int | None = None) -> dict[str, Any]:
    """Lab shell context. When ``project_id`` is set, replay comes from that project only."""

    ctx = neutral_lab_context()
    track = (
        get_latest_lab_replay_track_for_project(project_id)
        if project_id is not None
        else get_latest_lab_replay_track()
    )
    if track is None:
        return ctx

    frames_json, initial_json = build_lab_replay_payload(track)
    if not frames_json:
        return ctx

    n = len(frames_json)
    first_idx = int(frames_json[0]["frame_index"])
    ctx.update(
        {
            "total_frames": n,
            "initial_frame": first_idx,
            "initial_replay_phase": str(frames_json[0]["phase"]),
            "lab_replay_track_id": int(track.pk),
            "lab_replay_track_key": str(track.track_key),
            "lab_replay_frames_json": frames_json,
            "lab_initial_replay_frame_json": initial_json,
            "has_replay_frames": True,
        }
    )
    ui = dict(ctx["lab_ui_initial"])
    ui.update(
        {
            "frame": first_idx,
            "totalFrames": n,
            "hasReplayFrames": True,
            "replayTrackId": int(track.pk),
            "replayTrackKey": str(track.track_key),
        }
    )
    ctx["lab_ui_initial"] = ui
    single = _single_cell_overlay_matrix()
    ctx["lab_cell_overlay_matrix"] = single
    ctx["lab_cell_initial_classes"] = [single[0][0]]
    return ctx
