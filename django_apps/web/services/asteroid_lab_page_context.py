"""Default template context for the asteroid mining lab page (no demo payload)."""

from __future__ import annotations

from typing import Any, cast

from django.db.models import Count, Prefetch

from django_apps.asteroid_lab.models import ReplayFrame, ReplayTrack
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
    get_latest_lab_replay_track_for_project,
)
from django_apps.asteroid_lab.services.solver_run_lab_summary import solver_runs_for_lab_project

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


def serialize_replay_frame(frame: ReplayFrame) -> dict[str, Any]:
    """JSON-serializable legacy Lab ORM frame (cell lookup API only; not timeline source)."""

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
        "replay_track_metrics": {
            "frame_count": 0,
            "replay_truncated": False,
            "truncation_reason": None,
            "dropped_frame_count": None,
            "diagnostic_reason": None,
        },
        "lab_ui_initial": {
            "frame": initial_frame,
            "totalFrames": total_frames,
            "blueprintCode": "",
            "hasReplayFrames": False,
            "replayTrackId": None,
            "replayTrackKey": None,
        },
    }


def lab_page_context(*, project_id: int | None = None) -> dict[str, Any]:
    """Lab shell context. Product replay is one composed timeline per project."""

    ctx = neutral_lab_context()
    if project_id is None:
        return ctx

    ctx["runs"] = solver_runs_for_lab_project(int(project_id))

    track = get_latest_lab_replay_track_for_project(int(project_id))
    frames_json, track_metrics = build_lab_replay_frames_for_project(int(project_id))

    if not frames_json:
        if track is not None:
            ctx["lab_replay_track_id"] = int(track.pk)
            ctx["lab_replay_track_key"] = str(track.track_key)
        ctx["replay_track_metrics"] = track_metrics
        return ctx

    first = frames_json[0]
    n = len(frames_json)
    first_idx = int(first.get("frame_index", 0))
    initial_json = dict(first)

    ctx.update(
        {
            "total_frames": n,
            "initial_frame": first_idx,
            "initial_replay_phase": str(first.get("phase") or "—"),
            "lab_replay_frames_json": frames_json,
            "lab_initial_replay_frame_json": initial_json,
            "has_replay_frames": True,
            "replay_track_metrics": track_metrics,
        }
    )
    if track is not None:
        ctx["lab_replay_track_id"] = int(track.pk)
        ctx["lab_replay_track_key"] = str(track.track_key)

    ui = dict(ctx["lab_ui_initial"])
    ui.update(
        {
            "frame": first_idx,
            "totalFrames": n,
            "hasReplayFrames": True,
            "replayTrackId": int(track.pk) if track is not None else None,
            "replayTrackKey": str(track.track_key) if track is not None else None,
        }
    )
    ctx["lab_ui_initial"] = ui
    single = _single_cell_overlay_matrix()
    ctx["lab_cell_overlay_matrix"] = single
    ctx["lab_cell_initial_classes"] = [single[0][0]]
    return ctx
