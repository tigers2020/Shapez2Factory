"""Read-only Section B: RTTP optimization milestone cards (metrics-only)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.models import ReplayFrame, ReplayTrack, SolverRun
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.replay import event_types as et

DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK = "missing_optimization_milestone_track"
DIAGNOSTIC_EMPTY_OPTIMIZATION_MILESTONE_FRAMES = "empty_optimization_milestone_frames"
DIAGNOSTIC_INVALID_OPTIMIZATION_MILESTONE_PAYLOAD = "invalid_optimization_milestone_payload"

RTTP_MILESTONE_EVENT_TYPES: frozenset[str] = frozenset(
    {
        et.EVENT_TYPE_ROUTING_PROBE_STARTED,
        et.EVENT_TYPE_CANDIDATE_GENERATED,
        et.EVENT_TYPE_GA_BEST_UPDATED,
        et.EVENT_TYPE_ROUTING_COMMITTED,
    }
)


def _payload_has_forbidden_map_material(payload: dict[str, Any]) -> bool:
    """Reject Section B rows with renderable map bodies (not RTTP overlay snapshots)."""
    if "map_view" in payload:
        return True
    full_map = payload.get("full_map")
    return isinstance(full_map, list) and len(full_map) > 0


def _empty_track_metrics(
    *,
    track_key: str | None = None,
    source_solver_run_id: int | None = None,
    diagnostic_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "track_key": track_key,
        "frame_count": 0,
        "event_types": [],
        "replay_truncated": False,
        "truncation_reason": None,
        "dropped_frame_count": None,
        "diagnostic_reason": diagnostic_reason,
        "source_solver_run_id": source_solver_run_id,
    }


def _metrics_from_row(frame: ReplayFrame) -> dict[str, Any]:
    metrics = dict(frame.metric_snapshot_json or {})
    payload = dict(frame.frame_payload or {})
    extra = payload.get("metrics_json")
    if isinstance(extra, dict):
        metrics.update(extra)
    return metrics


def replay_frame_to_optimization_milestone_json(frame: ReplayFrame) -> dict[str, Any] | None:
    payload = dict(frame.frame_payload or {})
    if _payload_has_forbidden_map_material(payload):
        return None
    event_type = str(payload.get("event_type") or "")
    if event_type not in RTTP_MILESTONE_EVENT_TYPES:
        return None
    return {
        "frame_index": int(frame.frame_index),
        "phase": str(frame.phase),
        "event_type": event_type,
        "title": str(frame.title),
        "description": str(frame.description or ""),
        "inspector": {},
        "metrics": _metrics_from_row(frame),
    }


def _resolve_solver_run(
    project_id: int,
    *,
    run_key: str | None,
) -> SolverRun | None:
    qs = SolverRun.objects.filter(project_id=int(project_id)).order_by("-created_at", "-id")
    if run_key:
        qs = qs.filter(run_key=str(run_key).strip())
    return qs.first()


def build_lab_optimization_milestone_frames_for_project(
    project_id: int,
    *,
    run_key: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    run = _resolve_solver_run(int(project_id), run_key=run_key)
    if run is None:
        return [], _empty_track_metrics(
            diagnostic_reason=DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK
        )
    track_key = rttp_optimization_track_key(str(run.run_key))
    run_id = int(run.pk)
    track = ReplayTrack.objects.filter(
        project_id=int(project_id),
        track_key=track_key,
    ).first()
    if track is None:
        return [], _empty_track_metrics(
            track_key=track_key,
            source_solver_run_id=run_id,
            diagnostic_reason=DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK,
        )
    rows = ReplayFrame.objects.filter(replay_track_id=int(track.pk)).order_by("frame_index", "id")
    if not rows.exists():
        return [], _empty_track_metrics(
            track_key=track_key,
            source_solver_run_id=run_id,
            diagnostic_reason=DIAGNOSTIC_EMPTY_OPTIMIZATION_MILESTONE_FRAMES,
        )

    frames: list[dict[str, Any]] = []
    omitted = 0
    for row in rows:
        got = replay_frame_to_optimization_milestone_json(row)
        if got is None:
            omitted += 1
            continue
        frames.append(got)

    if not frames:
        return [], _empty_track_metrics(
            track_key=track_key,
            source_solver_run_id=run_id,
            diagnostic_reason=DIAGNOSTIC_INVALID_OPTIMIZATION_MILESTONE_PAYLOAD,
        )

    for visible_index, fr in enumerate(frames):
        fr["frame_index"] = visible_index

    event_types = [str(fr["event_type"]) for fr in frames]
    metrics: dict[str, Any] = {
        "track_key": track_key,
        "frame_count": len(frames),
        "event_types": event_types,
        "replay_truncated": False,
        "truncation_reason": None,
        "dropped_frame_count": omitted if omitted else None,
        "diagnostic_reason": None,
        "source_solver_run_id": run_id,
    }
    return frames, metrics


__all__ = [
    "DIAGNOSTIC_EMPTY_OPTIMIZATION_MILESTONE_FRAMES",
    "DIAGNOSTIC_INVALID_OPTIMIZATION_MILESTONE_PAYLOAD",
    "DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK",
    "RTTP_MILESTONE_EVENT_TYPES",
    "build_lab_optimization_milestone_frames_for_project",
    "replay_frame_to_optimization_milestone_json",
]
