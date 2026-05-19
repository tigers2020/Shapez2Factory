"""Read-only unified replay timeline for Lab page context (Phase 9E; presentation only)."""

from __future__ import annotations

from typing import Any, cast

from django.db.models import Count, Prefetch

from django_apps.asteroid_lab.models import ReplayFrame, ReplayTrack
from django_apps.asteroid_lab.optimization.replay_frame import OptimizationReplayFrame
from django_apps.asteroid_lab.replay import replay_limits
from django_apps.asteroid_lab.replay.lab_unified_adapter import (
    LabUnifiedAdapterError,
    lab_replay_row_to_unified,
)
from django_apps.asteroid_lab.replay.optimization_unified_adapter import (
    OptimizationUnifiedAdapterError,
    optimization_replay_frame_to_unified,
)
from django_apps.asteroid_lab.replay.projection_context import ReplayProjectionContext
from django_apps.asteroid_lab.replay.unified_dtos import ReplayCell, UnifiedReplayFrame
from django_apps.asteroid_lab.replay.unified_serialization import unified_replay_frame_to_json_dict
from django_apps.asteroid_lab.replay.unified_timeline_composer import compose_unified_timeline
from django_apps.asteroid_lab.services.dto import ReplayFrameRowDTO
from django_apps.asteroid_lab.services.optimization_replay_read import (
    optimization_replay_payload_for_project,
)
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY,
    deserialize_optimization_replay_frames_from_json,
)
from django_apps.asteroid_lab.snapshots.server_coords import map_bbox_dense_and_y

UNIFIED_REPLAY_LAB_PAYLOAD_KEY = "unified_replay"
UNIFIED_REPLAY_DIAGNOSTIC_REASON_KEY = "unified_replay_diagnostic_reason"


def _get_latest_lab_replay_track_for_project(project_id: int) -> ReplayTrack | None:
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
    """Derive adapter projection params from latest Lab replay cells (read-only)."""

    track = _get_latest_lab_replay_track_for_project(int(project_id))
    if track is None:
        return None
    ordered = list(track.frames.all())
    params = map_bbox_dense_and_y(_blueprint_rows_from_lab_maps(ordered))
    if params is None:
        return None
    return ReplayProjectionContext(server_xy_params=params)


def _fallback_cells_from_lab_unified(
    lab_unified: tuple[UnifiedReplayFrame, ...],
) -> tuple[ReplayCell, ...]:
    for frame in reversed(lab_unified):
        if frame.map_view.full_cells:
            return frame.map_view.full_cells
    return ()


def _lab_unified_frames_for_project(project_id: int) -> tuple[UnifiedReplayFrame, ...]:
    track = _get_latest_lab_replay_track_for_project(int(project_id))
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


def _optimization_unified_frames_for_project(
    project_id: int,
    *,
    context: ReplayProjectionContext | None,
    fallback_full_cells: tuple[ReplayCell, ...],
) -> tuple[UnifiedReplayFrame, ...]:
    track = optimization_replay_payload_for_project(int(project_id))
    metrics = track.get("metrics")
    if isinstance(metrics, dict) and metrics.get(OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY):
        return ()
    raw_frames = track.get("frames")
    if not isinstance(raw_frames, list):
        return ()
    opt_frames = deserialize_optimization_replay_frames_from_json(raw_frames)
    if opt_frames is None:
        return ()
    if context is None:
        return ()

    projection = ReplayProjectionContext(
        server_xy_params=context.server_xy_params,
        fallback_full_cells=fallback_full_cells,
    )
    out: list[UnifiedReplayFrame] = []
    for frame in opt_frames:
        if not isinstance(frame, OptimizationReplayFrame):
            continue
        try:
            out.append(
                optimization_replay_frame_to_unified(
                    frame,
                    context=projection,
                )
            )
        except OptimizationUnifiedAdapterError:
            continue
    return tuple(out)


def empty_unified_replay_payload(*, enabled: bool = False) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "frames": [],
        "track_metrics": {
            "frame_count": 0,
            "replay_truncated": False,
            "truncation_reason": None,
            "dropped_frame_count": None,
        },
        "diagnostic_reason": None,
    }


def _track_metrics_from_serialized_frames(frames: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(frames)
    if n == 0:
        return {
            "frame_count": 0,
            "replay_truncated": False,
            "truncation_reason": None,
            "dropped_frame_count": None,
        }
    last_metrics = dict(frames[-1].get("metrics") or {})
    truncated = any(bool(dict(fr.get("metrics") or {}).get("replay_truncated")) for fr in frames)
    return {
        "frame_count": n,
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
    }


def build_unified_replay_timeline_for_project(
    project_id: int,
    *,
    enabled: bool = True,
) -> dict[str, Any]:
    """Compose Lab + optimization unified frames for page JSON (never mutates sources)."""

    if not enabled:
        return empty_unified_replay_payload(enabled=False)

    lab_unified = _lab_unified_frames_for_project(int(project_id))
    projection = resolve_replay_projection_context_for_project(int(project_id))
    fallback = _fallback_cells_from_lab_unified(lab_unified)
    opt_unified = _optimization_unified_frames_for_project(
        int(project_id),
        context=projection,
        fallback_full_cells=fallback,
    )
    combined = compose_unified_timeline(
        lab_frames=lab_unified,
        optimization_frames=opt_unified,
        max_frames=replay_limits.MAX_UNIFIED_LAB_REPLAY_FRAMES,
    )
    serialized = [unified_replay_frame_to_json_dict(fr) for fr in combined]
    diagnostic: str | None = None
    if projection is None and opt_unified == () and lab_unified:
        diagnostic = "missing_server_xy_params_for_optimization_projection"
    return {
        "enabled": True,
        "frames": serialized,
        "track_metrics": _track_metrics_from_serialized_frames(serialized),
        "diagnostic_reason": diagnostic,
    }


__all__ = [
    "UNIFIED_REPLAY_DIAGNOSTIC_REASON_KEY",
    "UNIFIED_REPLAY_LAB_PAYLOAD_KEY",
    "build_unified_replay_timeline_for_project",
    "empty_unified_replay_payload",
    "resolve_replay_projection_context_for_project",
]
