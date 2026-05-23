"""Read-only product replay timeline for Lab page (Lab ORM + solver runtime frames)."""

from __future__ import annotations

from typing import Any, cast

from django.db.models import Count, Prefetch, Q

from django_apps.asteroid_lab.models import AsteroidMapInput, ReplayFrame, ReplayTrack, SolverRun
from django_apps.asteroid_lab.optimization.replay_track_keys import (
    RTTP_OPTIMIZATION_TRACK_SUFFIX,
    RTTP_TRACK_KEY_PREFIX,
)
from django_apps.asteroid_lab.replay import replay_limits
from django_apps.asteroid_lab.replay.lab_timeline_adapter import (
    LabTimelineAdapterError,
    lab_replay_row_to_timeline_frame,
)
from django_apps.asteroid_lab.replay.projection_context import ReplayProjectionContext
from django_apps.asteroid_lab.replay.timeline_composer import compose_replay_timeline
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayTimelineFrame
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_timeline_frame_from_json_dict,
    replay_timeline_frame_to_json_dict,
)
from django_apps.asteroid_lab.services.dto import ReplayFrameRowDTO
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    build_lab_optimization_milestone_frames_for_project,
)
from django_apps.asteroid_lab.services.lab_unified_replay_append import (
    append_algorithm_frames_to_unified_lab_replay,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY,
)
from django_apps.asteroid_lab.snapshots.server_coords import map_bbox_dense_and_y

REPLAY_DIAGNOSTIC_REASON_KEY = "replay_diagnostic_reason"
DIAGNOSTIC_RTTP_TRACK_BLOCKED_LAB_TIMELINE = "rttp_track_blocked_lab_timeline"
DIAGNOSTIC_NO_REPLAY_FRAMES = "no_replay_frames"
DIAGNOSTIC_LAB_TIMELINE_ADAPTER_FILTERED_ALL = "lab_timeline_adapter_filtered_all"
INSPECTION_TRACK_KEY_PREFIX = "inspection-"


def _empty_track_metrics() -> dict[str, Any]:
    return {
        "frame_count": 0,
        "replay_truncated": False,
        "truncation_reason": None,
        "dropped_frame_count": None,
        "diagnostic_reason": None,
    }


def get_latest_lab_replay_track_for_project(project_id: int) -> ReplayTrack | None:
    """Latest replay track (with frames) for one project (display-only)."""

    ordered_frames = ReplayFrame.objects.order_by("frame_index", "id")
    return cast(
        ReplayTrack | None,
        ReplayTrack.objects.filter(project_id=int(project_id))
        .exclude(
            Q(track_key__startswith=RTTP_TRACK_KEY_PREFIX)
            | Q(track_key__endswith=RTTP_OPTIMIZATION_TRACK_SUFFIX)
        )
        .annotate(_frame_count=Count("frames"))
        .filter(_frame_count__gt=0)
        .order_by("-created_at", "-id")
        .prefetch_related(Prefetch("frames", queryset=ordered_frames))
        .first(),
    )


def _frame_row_from_model(frame: ReplayFrame) -> ReplayFrameRowDTO:
    return ReplayFrameRowDTO(
        id=int(frame.pk),
        frame_index=int(frame.frame_index),
        frame_key=str(frame.frame_key),
        phase=str(frame.phase),
        title=str(frame.title),
        description=str(frame.description or ""),
        frame_payload=dict(frame.frame_payload or {}),
        cell_overlay_json=dict(frame.cell_overlay_json or {}),
        metric_snapshot_json=dict(frame.metric_snapshot_json or {}),
        is_placeholder=bool(frame.is_placeholder),
        is_keyframe=bool(frame.is_keyframe),
    )


def _server_xy_params_from_map_input(inp: AsteroidMapInput) -> tuple[int, int] | None:
    """Blueprint ``BP.Entries`` bbox (same source as reconstruction)."""

    decoded = dict(inp.decoded_json or {})
    bp = decoded.get("BP")
    if not isinstance(bp, dict):
        return None
    entries = bp.get("Entries")
    if not isinstance(entries, list):
        return None
    rows: list[dict[str, int]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        x, y = item.get("X"), item.get("Y")
        if isinstance(x, int) and isinstance(y, int):
            rows.append({"X": x, "Y": y})
    return map_bbox_dense_and_y(rows)


def _server_xy_params_from_latest_solver_run(project_id: int) -> tuple[int, int] | None:
    run = (
        SolverRun.objects.filter(project_id=int(project_id)).order_by("-created_at", "-id").first()
    )
    if run is None:
        return None
    config = dict(run.config_json or {})
    raw = config.get(SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY)
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        return None
    try:
        return (int(raw[0]), int(raw[1]))
    except (TypeError, ValueError):
        return None


def _server_xy_params_from_lab_replay_track(project_id: int) -> tuple[int, int] | None:
    track = get_latest_lab_replay_track_for_project(int(project_id))
    if track is None:
        return None
    ordered = list(track.frames.all())
    return map_bbox_dense_and_y(_blueprint_rows_from_lab_maps(ordered))


def _blueprint_rows_from_lab_maps(frames: list[ReplayFrame]) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for frame in frames:
        payload = frame.frame_payload or {}
        full_map = payload.get("full_map")
        if not isinstance(full_map, list):
            co = frame.cell_overlay_json or {}
            cells = co.get("cells")
            full_map = cells if isinstance(cells, list) else []
        for cell in full_map:
            if not isinstance(cell, dict):
                continue
            x, y = cell.get("x"), cell.get("y")
            if isinstance(x, int) and isinstance(y, int):
                rows.append({"X": x, "Y": y})
    return rows


def resolve_replay_projection_context_for_project(
    project_id: int,
) -> ReplayProjectionContext | None:
    """Derive adapter projection params (reconstruction-aligned; read-only)."""

    params = _server_xy_params_from_latest_solver_run(int(project_id))
    if params is None:
        inp = (
            AsteroidMapInput.objects.filter(project_id=int(project_id))
            .order_by("-created_at", "-id")
            .first()
        )
        if inp is not None:
            params = _server_xy_params_from_map_input(inp)
    if params is None:
        params = _server_xy_params_from_lab_replay_track(int(project_id))
    if params is None:
        return None
    return ReplayProjectionContext(server_xy_params=params)


def _solver_runtime_timeline_frames_for_project(
    project_id: int,
) -> tuple[ReplayTimelineFrame, ...]:
    """Load persisted solver runtime replay frames from latest SolverRun.config_json."""
    run = (
        SolverRun.objects.filter(project_id=int(project_id)).order_by("-created_at", "-id").first()
    )
    if run is None:
        return ()
    config = dict(run.config_json or {})
    raw = config.get(SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY)
    if not isinstance(raw, list) or not raw:
        return ()
    out: list[ReplayTimelineFrame] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            out.append(replay_timeline_frame_from_json_dict(item))
        except Exception:  # noqa: BLE001
            continue
    return tuple(out)


def _lab_timeline_frames_from_track(track: ReplayTrack | None) -> tuple[ReplayTimelineFrame, ...]:
    if track is None:
        return ()
    ordered = list(track.frames.all())
    out: list[ReplayTimelineFrame] = []
    for frame in ordered:
        try:
            out.append(lab_replay_row_to_timeline_frame(_frame_row_from_model(frame)))
        except LabTimelineAdapterError:
            continue
    return tuple(out)


def _latest_inspection_replay_track(project_id: int) -> ReplayTrack | None:
    ordered_frames = ReplayFrame.objects.order_by("frame_index", "id")
    return cast(
        ReplayTrack | None,
        ReplayTrack.objects.filter(
            project_id=int(project_id),
            track_key__startswith=INSPECTION_TRACK_KEY_PREFIX,
        )
        .annotate(_frame_count=Count("frames"))
        .filter(_frame_count__gt=0)
        .order_by("-created_at", "-id")
        .prefetch_related(Prefetch("frames", queryset=ordered_frames))
        .first(),
    )


def _lab_replay_diagnostic_reason(project_id: int, *, composed_count: int) -> str | None:
    if composed_count > 0:
        return None
    pid = int(project_id)
    has_inspection = (
        ReplayTrack.objects.filter(
            project_id=pid,
            track_key__startswith=INSPECTION_TRACK_KEY_PREFIX,
        )
        .annotate(_fc=Count("frames"))
        .filter(_fc__gt=0)
        .exists()
    )
    has_rttp_orm_frames = (
        ReplayTrack.objects.filter(project_id=pid)
        .filter(
            Q(track_key__startswith=RTTP_TRACK_KEY_PREFIX)
            | Q(track_key__endswith=RTTP_OPTIMIZATION_TRACK_SUFFIX)
        )
        .annotate(_fc=Count("frames"))
        .filter(_fc__gt=0)
        .exists()
    )
    if has_inspection and has_rttp_orm_frames:
        return DIAGNOSTIC_RTTP_TRACK_BLOCKED_LAB_TIMELINE
    if (
        ReplayTrack.objects.filter(project_id=pid)
        .annotate(_fc=Count("frames"))
        .filter(_fc__gt=0)
        .exists()
    ):
        return DIAGNOSTIC_LAB_TIMELINE_ADAPTER_FILTERED_ALL
    return DIAGNOSTIC_NO_REPLAY_FRAMES


def _lab_timeline_frames_for_project(project_id: int) -> tuple[ReplayTimelineFrame, ...]:
    track = get_latest_lab_replay_track_for_project(int(project_id))
    out = _lab_timeline_frames_from_track(track)
    if out:
        return out
    fallback = _latest_inspection_replay_track(int(project_id))
    if fallback is not None and (track is None or int(fallback.pk) != int(track.pk)):
        return _lab_timeline_frames_from_track(fallback)
    return out


def _track_metrics_from_serialized_frames(
    frames: list[dict[str, Any]],
    *,
    diagnostic_reason: str | None,
) -> dict[str, Any]:
    if not frames:
        out = _empty_track_metrics()
        if diagnostic_reason:
            out["diagnostic_reason"] = diagnostic_reason
        return out
    last_metrics = dict(frames[-1].get("metrics") or {})
    truncated = any(bool(dict(fr.get("metrics") or {}).get("replay_truncated")) for fr in frames)
    return {
        "frame_count": len(frames),
        "replay_truncated": truncated,
        "truncation_reason": (
            str(last_metrics["truncation_reason"])
            if truncated and last_metrics.get("truncation_reason") is not None
            else None
        ),
        "dropped_frame_count": (
            last_metrics.get("dropped_frame_count")
            if truncated and last_metrics.get("dropped_frame_count") is not None
            else None
        ),
        "diagnostic_reason": diagnostic_reason,
    }


def build_lab_replay_frames_for_project(
    project_id: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compose Lab + solver runtime replay into product timeline JSON (never mutates sources)."""

    lab_frames = _lab_timeline_frames_for_project(int(project_id))
    runtime_frames = _solver_runtime_timeline_frames_for_project(int(project_id))
    combined = compose_replay_timeline(
        lab_frames=(*lab_frames, *runtime_frames),
        max_frames=replay_limits.MAX_LAB_REPLAY_TIMELINE_FRAMES,
    )
    serialized = [replay_timeline_frame_to_json_dict(fr) for fr in combined]
    milestone_frames, _milestone_metrics = build_lab_optimization_milestone_frames_for_project(
        int(project_id),
        run_key=None,
    )
    serialized = append_algorithm_frames_to_unified_lab_replay(serialized, milestone_frames)
    diagnostic = _lab_replay_diagnostic_reason(int(project_id), composed_count=len(serialized))
    metrics = _track_metrics_from_serialized_frames(serialized, diagnostic_reason=diagnostic)
    return serialized, metrics


__all__ = [
    "DIAGNOSTIC_NO_REPLAY_FRAMES",
    "DIAGNOSTIC_RTTP_TRACK_BLOCKED_LAB_TIMELINE",
    "REPLAY_DIAGNOSTIC_REASON_KEY",
    "build_lab_replay_frames_for_project",
    "get_latest_lab_replay_track_for_project",
    "resolve_replay_projection_context_for_project",
    "_solver_runtime_timeline_frames_for_project",
]
