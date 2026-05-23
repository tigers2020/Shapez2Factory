"""Project :rttp write-buffer rows into full-snapshot Lab replay frames (output-only)."""

from __future__ import annotations

import copy
from typing import Any

from django_apps.asteroid_lab.models import ReplayFrame, ReplayTrack, SolverRun
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT,
    EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT,
    EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT,
    EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT,
    is_rttp_milestone_event_type,
    normalize_rttp_milestone_event_type,
)
from django_apps.asteroid_lab.replay.projection_context import lab_xy_from_replay_cell

_RECONSTRUCTION_COMPLETED = "reconstruction.completed"

# Finer interleave: each RTTP milestone inserts after its lifecycle predecessor.
_RTTP_ANCHOR_AFTER_EVENT: dict[str, str] = {
    EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT: _RECONSTRUCTION_COMPLETED,
    EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT: EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT,
    EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT: EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT,
    EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT: EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT,
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


def _is_asteroid_footprint_kind(kind: str) -> bool:
    return kind.startswith("asteroid") or kind == "mineable"


def _base_map_overlay_anchors(
    base_map_view: dict[str, Any],
) -> frozenset[tuple[int, int]]:
    """Lab ``(x,y)`` anchors from ``full_cells`` (island-local, PR-F Wave C)."""

    lab_coords: set[tuple[int, int]] = set()
    full_cells = base_map_view.get("full_cells")
    if not isinstance(full_cells, list):
        return frozenset()
    for raw in full_cells:
        if not isinstance(raw, dict) or "x" not in raw or "y" not in raw:
            continue
        kind = str(raw.get("kind") or raw.get("cell_kind") or "")
        if not _is_asteroid_footprint_kind(kind):
            continue
        lab_coords.add((int(raw["x"]), int(raw["y"])))
    return frozenset(lab_coords)


def clip_overlay_cells_to_base_map_domain(
    overlay_cells: list[dict[str, Any]],
    base_map_view: dict[str, Any],
) -> list[dict[str, Any]]:
    lab_anchors = _base_map_overlay_anchors(base_map_view)
    if not lab_anchors:
        return []
    clipped: list[dict[str, Any]] = []
    for cell in overlay_cells:
        if "x" not in cell or "y" not in cell:
            continue
        ox, oy = int(cell["x"]), int(cell["y"])
        lab_xy = (ox, oy) if (ox, oy) in lab_anchors else lab_xy_from_replay_cell(ox, oy)
        if lab_xy in lab_anchors:
            projected = dict(cell)
            projected["x"] = lab_xy[0]
            projected["y"] = lab_xy[1]
            clipped.append(projected)
    return clipped


def project_rttp_row_to_product_frame(
    row: dict[str, Any],
    *,
    base_map_view: dict[str, Any],
) -> dict[str, Any]:
    mv = copy.deepcopy(base_map_view)
    overlay_from_row = _overlay_cells_from_cell_overlay_json(
        row.get("cell_overlay_json") if isinstance(row.get("cell_overlay_json"), dict) else None
    )
    clipped = clip_overlay_cells_to_base_map_domain(overlay_from_row, base_map_view)
    if clipped:
        mv["overlay_cells"] = clipped
    else:
        mv.setdefault("overlay_cells", [])
    return {
        "frame_index": 0,
        "phase": str(row.get("phase") or ""),
        "event_type": normalize_rttp_milestone_event_type(str(row.get("event_type") or "")),
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
        event_type = normalize_rttp_milestone_event_type(str(row.get("event_type") or ""))
        if not is_rttp_milestone_event_type(str(row.get("event_type") or "")):
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
    "clip_overlay_cells_to_base_map_domain",
    "frame_has_renderable_map",
    "interleave_rttp_snapshot_frames",
    "last_renderable_frame_index",
    "load_rttp_compose_rows_for_project",
    "project_rttp_row_to_product_frame",
    "resolve_insert_index",
]
