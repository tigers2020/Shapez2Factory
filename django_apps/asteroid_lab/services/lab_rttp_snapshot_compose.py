"""Project :rttp write-buffer rows into full-snapshot Lab replay frames (output-only)."""

from __future__ import annotations

import copy
from typing import Any

from django_apps.asteroid_lab.models import ReplayFrame, ReplayTrack, SolverRun
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)

_RECONSTRUCTION_COMPLETED = "reconstruction.completed"

# Finer interleave: each RTTP milestone inserts after its lifecycle predecessor.
_RTTP_ANCHOR_AFTER_EVENT: dict[str, str] = {
    et.EVENT_TYPE_ROUTING_PROBE_STARTED: _RECONSTRUCTION_COMPLETED,
    et.EVENT_TYPE_CANDIDATE_GENERATED: et.EVENT_TYPE_ROUTING_PROBE_STARTED,
    et.EVENT_TYPE_GA_BEST_UPDATED: et.EVENT_TYPE_CANDIDATE_GENERATED,
    et.EVENT_TYPE_ROUTING_COMMITTED: et.EVENT_TYPE_GA_BEST_UPDATED,
}


def frame_has_renderable_map(frame: dict[str, Any]) -> bool:
    mv = frame.get("map_view")
    if not isinstance(mv, dict):
        return False
    full_cells = mv.get("full_cells")
    if isinstance(full_cells, list) and len(full_cells) > 0:
        return True
    cell_delta = mv.get("cell_delta")
    if isinstance(cell_delta, list) and len(cell_delta) > 0:
        return True
    overlay = mv.get("overlay_cells")
    return isinstance(overlay, list) and len(overlay) > 0


def last_renderable_frame_index(frames: list[dict[str, Any]]) -> int:
    for idx in range(len(frames) - 1, -1, -1):
        if frame_has_renderable_map(frames[idx]):
            return idx
    return max(0, len(frames) - 1)


def _find_reconstruction_completed_index(frames: list[dict[str, Any]]) -> int | None:
    for idx in range(len(frames) - 1, -1, -1):
        if str(frames[idx].get("event_type") or "") == _RECONSTRUCTION_COMPLETED:
            if frame_has_renderable_map(frames[idx]):
                return idx
    return None


def resolve_insert_index(base_frames: list[dict[str, Any]]) -> int:
    """Fallback anchor: reconstruction.completed, else last renderable frame."""
    if not base_frames:
        return 0
    recon = _find_reconstruction_completed_index(base_frames)
    if recon is not None:
        return recon
    return last_renderable_frame_index(base_frames)


def _find_anchor_index_for_rttp_row(
    unified: list[dict[str, Any]],
    event_type: str,
) -> int:
    preferred = _RTTP_ANCHOR_AFTER_EVENT.get(event_type)
    if preferred is not None:
        for idx in range(len(unified) - 1, -1, -1):
            if str(unified[idx].get("event_type") or "") == preferred:
                if frame_has_renderable_map(unified[idx]):
                    return idx
    return resolve_insert_index(unified)


def _map_view_at_index(frames: list[dict[str, Any]], index: int) -> dict[str, Any]:
    if not frames:
        return {}
    safe = max(0, min(index, len(frames) - 1))
    if frame_has_renderable_map(frames[safe]):
        return dict(frames[safe].get("map_view") or {})
    return dict(frames[last_renderable_frame_index(frames)].get("map_view") or {})


def _overlay_cells_from_cell_overlay_json(overlay: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(overlay, dict):
        return []
    cells = overlay.get("cells")
    if isinstance(cells, list):
        return [dict(c) for c in cells if isinstance(c, dict)]
    return []


def project_rttp_row_to_product_frame(
    row: dict[str, Any],
    *,
    base_map_view: dict[str, Any],
) -> dict[str, Any]:
    mv = copy.deepcopy(base_map_view)
    overlay_from_row = _overlay_cells_from_cell_overlay_json(
        row.get("cell_overlay_json") if isinstance(row.get("cell_overlay_json"), dict) else None
    )
    if overlay_from_row:
        mv["overlay_cells"] = overlay_from_row
    else:
        mv.setdefault("overlay_cells", [])
    return {
        "frame_index": 0,
        "phase": str(row.get("phase") or ""),
        "event_type": str(row.get("event_type") or ""),
        "title": str(row.get("title") or ""),
        "description": str(row.get("description") or ""),
        "map_view": mv,
        "inspector": dict(row.get("inspector") or {}),
        "metrics": dict(row.get("metrics") or {}),
    }


def interleave_rttp_snapshot_frames(
    base_frames: list[dict[str, Any]],
    rttp_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unified: list[dict[str, Any]] = [copy.deepcopy(fr) for fr in base_frames]
    if not rttp_rows:
        for i, fr in enumerate(unified):
            fr["frame_index"] = i
        return unified

    if not unified or not any(frame_has_renderable_map(fr) for fr in unified):
        for i, fr in enumerate(unified):
            fr["frame_index"] = i
        return unified

    for row in rttp_rows:
        event_type = str(row.get("event_type") or "")
        if event_type not in RTTP_MILESTONE_EVENT_TYPES:
            continue
        insert_at = _find_anchor_index_for_rttp_row(unified, event_type)
        base_mv = _map_view_at_index(unified, insert_at)
        projected = project_rttp_row_to_product_frame(row, base_map_view=base_mv)
        unified.insert(insert_at + 1, projected)

    for i, fr in enumerate(unified):
        fr["frame_index"] = i
    return unified


def load_rttp_compose_rows_for_project(
    project_id: int,
    *,
    run_key: str | None = None,
) -> list[dict[str, Any]]:
    """Read :rttp ORM rows for compose (write buffer; not product timeline)."""
    qs = SolverRun.objects.filter(project_id=int(project_id)).order_by("-id")
    if run_key is not None:
        qs = qs.filter(run_key=str(run_key))
    run = qs.first()
    if run is None:
        return []
    track = ReplayTrack.objects.filter(
        project_id=int(project_id),
        track_key=rttp_optimization_track_key(str(run.run_key)),
    ).first()
    if track is None:
        return []
    rows: list[dict[str, Any]] = []
    for frame in ReplayFrame.objects.filter(replay_track_id=track.id).order_by("frame_index"):
        payload = dict(frame.frame_payload or {})
        rows.append(
            {
                "event_type": str(payload.get("event_type") or ""),
                "phase": str(frame.phase),
                "title": str(frame.title),
                "description": str(frame.description or ""),
                "metrics": dict(frame.metric_snapshot_json or {}),
                "cell_overlay_json": dict(frame.cell_overlay_json or {}),
                "inspector": {},
            }
        )
    return rows


__all__ = [
    "frame_has_renderable_map",
    "interleave_rttp_snapshot_frames",
    "last_renderable_frame_index",
    "load_rttp_compose_rows_for_project",
    "project_rttp_row_to_product_frame",
    "resolve_insert_index",
]
