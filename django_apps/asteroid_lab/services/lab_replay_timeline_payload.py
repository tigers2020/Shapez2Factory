"""Read-only product replay timeline for Lab page (Lab ORM + solver runtime frames)."""

from __future__ import annotations

from typing import Any, cast

from django.db.models import Count, Prefetch

from django_apps.asteroid_lab.models import AsteroidMapInput, ReplayFrame, ReplayTrack, SolverRun
from django_apps.asteroid_lab.replay import replay_limits
from django_apps.asteroid_lab.replay.lab_unified_adapter import (
    LabUnifiedAdapterError,
    lab_replay_row_to_unified,
)
from django_apps.asteroid_lab.replay.projection_context import ReplayProjectionContext
from django_apps.asteroid_lab.replay.unified_dtos import UnifiedReplayFrame
from django_apps.asteroid_lab.replay.unified_serialization import (
    unified_replay_frame_from_json_dict,
    unified_replay_frame_to_json_dict,
)
from django_apps.asteroid_lab.replay.unified_timeline_composer import compose_unified_timeline
from django_apps.asteroid_lab.services.dto import ReplayFrameRowDTO
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY,
)
from django_apps.asteroid_lab.snapshots.server_coords import map_bbox_dense_and_y

REPLAY_DIAGNOSTIC_REASON_KEY = "replay_diagnostic_reason"


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


def _solver_runtime_unified_frames_for_project(
    project_id: int,
) -> tuple[UnifiedReplayFrame, ...]:
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
    out: list[UnifiedReplayFrame] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            out.append(unified_replay_frame_from_json_dict(item))
        except Exception:  # noqa: BLE001
            continue
    return tuple(out)


def _lab_unified_frames_for_project(project_id: int) -> tuple[UnifiedReplayFrame, ...]:
    track = get_latest_lab_replay_track_for_project(int(project_id))
    if track is None:
        return ()
    ordered = list(track.frames.all())
    out: list[UnifiedReplayFrame] = []
    for frame in ordered:
        try:
            out.append(lab_replay_row_to_unified(_frame_row_from_model(frame)))
        except LabUnifiedAdapterError:
            continue
    return tuple(out)


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
    """Compose Lab + solver runtime replay into unified product JSON (never mutates sources)."""

    lab_unified = _lab_unified_frames_for_project(int(project_id))
    solver_unified = _solver_runtime_unified_frames_for_project(int(project_id))
    combined = compose_unified_timeline(
        lab_frames=(*lab_unified, *solver_unified),
        max_frames=replay_limits.MAX_UNIFIED_LAB_REPLAY_FRAMES,
    )
    serialized = [unified_replay_frame_to_json_dict(fr) for fr in combined]
    metrics = _track_metrics_from_serialized_frames(serialized, diagnostic_reason=None)
    return serialized, metrics


__all__ = [
    "REPLAY_DIAGNOSTIC_REASON_KEY",
    "build_lab_replay_frames_for_project",
    "get_latest_lab_replay_track_for_project",
    "resolve_replay_projection_context_for_project",
    "_solver_runtime_unified_frames_for_project",
]
