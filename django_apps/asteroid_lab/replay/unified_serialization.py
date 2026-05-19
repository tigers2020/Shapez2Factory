"""JSON serialization for unified replay DTOs (Phase 9A)."""

from __future__ import annotations

import json
from typing import Any, Mapping

from django_apps.asteroid_lab.replay.unified_dtos import (
    ReplayAnnotation,
    ReplayBBox,
    ReplayCell,
    ReplayCellDelta,
    ReplayMapView,
    ReplayOverlayCell,
    UnifiedReplayFrame,
)
from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType, ReplayPhase


class UnifiedReplayDeserializationError(ValueError):
    """Raised when wire JSON violates the unified replay contract."""


def _require_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise UnifiedReplayDeserializationError(f"{field} must be int")
    return value


def _mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return dict(value)


def replay_bbox_to_json_dict(bbox: ReplayBBox) -> dict[str, int]:
    return {
        "min_x": int(bbox.min_x),
        "min_y": int(bbox.min_y),
        "max_x": int(bbox.max_x),
        "max_y": int(bbox.max_y),
    }


def replay_bbox_from_json_dict(data: object) -> ReplayBBox:
    if not isinstance(data, dict):
        raise UnifiedReplayDeserializationError("bbox must be object")
    return ReplayBBox(
        min_x=_require_int(data.get("min_x"), field="bbox.min_x"),
        min_y=_require_int(data.get("min_y"), field="bbox.min_y"),
        max_x=_require_int(data.get("max_x"), field="bbox.max_x"),
        max_y=_require_int(data.get("max_y"), field="bbox.max_y"),
    )


def _cell_from_dict(data: dict[str, Any]) -> ReplayCell:
    return ReplayCell(
        x=_require_int(data.get("x"), field="cell.x"),
        y=_require_int(data.get("y"), field="cell.y"),
        kind=str(data.get("kind") or ""),
        transport=str(data.get("transport") or ""),
    )


def _cell_delta_from_dict(data: dict[str, Any]) -> ReplayCellDelta:
    return ReplayCellDelta(
        x=_require_int(data.get("x"), field="cell_delta.x"),
        y=_require_int(data.get("y"), field="cell_delta.y"),
        kind=str(data.get("kind") or ""),
        transport=str(data.get("transport") or ""),
        op=str(data.get("op") or "set"),
    )


def _overlay_from_dict(data: dict[str, Any]) -> ReplayOverlayCell:
    return ReplayOverlayCell(
        x=_require_int(data.get("x"), field="overlay.x"),
        y=_require_int(data.get("y"), field="overlay.y"),
        kind=str(data.get("kind") or ""),
        transport=str(data.get("transport") or ""),
    )


def _annotation_from_dict(data: dict[str, Any]) -> ReplayAnnotation:
    return ReplayAnnotation(
        x=_require_int(data.get("x"), field="annotation.x"),
        y=_require_int(data.get("y"), field="annotation.y"),
        label=str(data.get("label") or ""),
    )


def _tuple_from_list(raw: object, factory: Any) -> tuple[Any, ...]:
    if not isinstance(raw, list):
        return ()
    out: list[Any] = []
    for item in raw:
        if not isinstance(item, dict):
            raise UnifiedReplayDeserializationError("cell list items must be objects")
        out.append(factory(dict(item)))
    return tuple(out)


def replay_map_view_to_json_dict(map_view: ReplayMapView) -> dict[str, Any]:
    return {
        "base_ref": map_view.base_ref,
        "full_cells": [
            {"x": c.x, "y": c.y, "kind": c.kind, "transport": c.transport} for c in map_view.full_cells
        ],
        "cell_delta": [
            {
                "x": c.x,
                "y": c.y,
                "kind": c.kind,
                "transport": c.transport,
                "op": c.op,
            }
            for c in map_view.cell_delta
        ],
        "overlay_cells": [
            {"x": c.x, "y": c.y, "kind": c.kind, "transport": c.transport}
            for c in map_view.overlay_cells
        ],
        "annotations": [{"x": a.x, "y": a.y, "label": a.label} for a in map_view.annotations],
        "bbox": replay_bbox_to_json_dict(map_view.bbox),
    }


def replay_map_view_from_json_dict(data: object) -> ReplayMapView:
    if not isinstance(data, dict):
        raise UnifiedReplayDeserializationError("map_view must be object")
    base_ref = data.get("base_ref")
    ref: str | None
    if base_ref is None:
        ref = None
    else:
        ref = str(base_ref) or None
    return ReplayMapView(
        base_ref=ref,
        full_cells=_tuple_from_list(data.get("full_cells"), _cell_from_dict),  # type: ignore[arg-type]
        cell_delta=_tuple_from_list(data.get("cell_delta"), _cell_delta_from_dict),  # type: ignore[arg-type]
        overlay_cells=_tuple_from_list(data.get("overlay_cells"), _overlay_from_dict),  # type: ignore[arg-type]
        annotations=_tuple_from_list(data.get("annotations"), _annotation_from_dict),  # type: ignore[arg-type]
        bbox=replay_bbox_from_json_dict(data.get("bbox")),
    )


def unified_replay_frame_to_json_dict(frame: UnifiedReplayFrame) -> dict[str, Any]:
    return {
        "frame_index": int(frame.frame_index),
        "phase": frame.phase.value,
        "event_type": frame.event_type.value,
        "title": str(frame.title),
        "description": str(frame.description),
        "map_view": replay_map_view_to_json_dict(frame.map_view),
        "inspector": dict(frame.inspector),
        "metrics": dict(frame.metrics),
    }


def parse_replay_phase(raw: object) -> ReplayPhase:
    if not isinstance(raw, str):
        raise UnifiedReplayDeserializationError("phase must be string")
    try:
        return ReplayPhase(raw)
    except ValueError as exc:
        raise UnifiedReplayDeserializationError(f"unknown phase: {raw!r}") from exc


def parse_replay_event_type(raw: object) -> ReplayEventType:
    if not isinstance(raw, str):
        raise UnifiedReplayDeserializationError("event_type must be string")
    try:
        return ReplayEventType(raw)
    except ValueError as exc:
        raise UnifiedReplayDeserializationError(f"unknown event_type: {raw!r}") from exc


def unified_replay_frame_from_json_dict(data: Mapping[str, Any]) -> UnifiedReplayFrame:
    if "map_view" not in data:
        raise UnifiedReplayDeserializationError("map_view is required")
    return UnifiedReplayFrame(
        frame_index=_require_int(data.get("frame_index"), field="frame_index"),
        phase=parse_replay_phase(data.get("phase")),
        event_type=parse_replay_event_type(data.get("event_type")),
        title=str(data.get("title") or ""),
        description=str(data.get("description") or ""),
        map_view=replay_map_view_from_json_dict(data.get("map_view")),
        inspector=_mapping(data.get("inspector")),
        metrics=_mapping(data.get("metrics")),
    )


def unified_replay_frame_json_round_trip(frame: UnifiedReplayFrame) -> UnifiedReplayFrame:
    """Serialize to JSON text and back (contract helper for tests)."""
    payload = unified_replay_frame_to_json_dict(frame)
    text = json.dumps(payload, default=str)
    restored = json.loads(text)
    if not isinstance(restored, dict):
        raise UnifiedReplayDeserializationError("round-trip did not yield object")
    return unified_replay_frame_from_json_dict(restored)
