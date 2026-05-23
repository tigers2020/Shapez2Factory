"""Append RTTP algorithm milestone dicts onto unified lab_replay_frames_json (output-only)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.replay.replay_render_modes import RENDER_MODE_INHERITED_SNAPSHOT

INSPECTOR_KIND_OPTIMIZATION_MILESTONE = "optimization_milestone"

_EMPTY_MAP_VIEW: dict[str, Any] = {
    "base_ref": None,
    "full_cells": [],
    "cell_delta": [],
    "overlay_cells": [],
    "annotations": [],
    "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
}


def _frame_has_renderable_map_cells(frame: dict[str, Any]) -> bool:
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


def last_renderable_map_frame_index(map_frames: list[dict[str, Any]]) -> int:
    for idx in range(len(map_frames) - 1, -1, -1):
        if _frame_has_renderable_map_cells(map_frames[idx]):
            return idx
    return max(0, len(map_frames) - 1)


def _algorithm_frame_from_milestone(
    milestone: dict[str, Any],
    *,
    base_frame_index: int,
) -> dict[str, Any]:
    inspector = dict(milestone.get("inspector") or {})
    inspector.setdefault("kind", INSPECTOR_KIND_OPTIMIZATION_MILESTONE)
    return {
        "frame_index": 0,
        "phase": str(milestone.get("phase") or ""),
        "event_type": str(milestone.get("event_type") or ""),
        "title": str(milestone.get("title") or ""),
        "description": str(milestone.get("description") or ""),
        "render_mode": RENDER_MODE_INHERITED_SNAPSHOT,
        "base_frame_index": int(base_frame_index),
        "map_view": dict(_EMPTY_MAP_VIEW),
        "inspector": inspector,
        "metrics": dict(milestone.get("metrics") or {}),
    }


def append_algorithm_frames_to_unified_lab_replay(
    map_frames: list[dict[str, Any]],
    algorithm_milestones: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unified: list[dict[str, Any]] = [dict(fr) for fr in map_frames]
    if not algorithm_milestones:
        for i, fr in enumerate(unified):
            fr["frame_index"] = i
        return unified
    base_idx = last_renderable_map_frame_index(unified)
    for m in algorithm_milestones:
        unified.append(_algorithm_frame_from_milestone(m, base_frame_index=base_idx))
    for i, fr in enumerate(unified):
        fr["frame_index"] = i
    return unified


__all__ = [
    "append_algorithm_frames_to_unified_lab_replay",
    "last_renderable_map_frame_index",
]
