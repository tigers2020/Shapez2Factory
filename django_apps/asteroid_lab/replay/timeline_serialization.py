"""JSON serialization for Lab replay timeline DTOs (Phase 9A)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from django_apps.asteroid_lab.replay.map_height_layer import (
    resolve_replay_height_layer,
    wire_explicit_height_layer,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayAnnotation,
    ReplayBBox,
    ReplayCell,
    ReplayCellDelta,
    ReplayMapView,
    ReplayOverlayCell,
    ReplayTimelineFrame,
)


class ReplayTimelineDeserializationError(ValueError):
    """Raised when wire JSON violates the replay timeline contract."""


def _require_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReplayTimelineDeserializationError(f"{field} must be int")
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
        raise ReplayTimelineDeserializationError("bbox must be object")
    return ReplayBBox(
        min_x=_require_int(data.get("min_x"), field="bbox.min_x"),
        min_y=_require_int(data.get("min_y"), field="bbox.min_y"),
        max_x=_require_int(data.get("max_x"), field="bbox.max_x"),
        max_y=_require_int(data.get("max_y"), field="bbox.max_y"),
    )


def _wire_kind(data: dict[str, Any]) -> str:
    return str(data.get("kind") or data.get("cell_kind") or "")


def _wire_transport(data: dict[str, Any]) -> str:
    return str(data.get("transport") or data.get("transport_kind") or "")


def _cell_from_dict(data: dict[str, Any]) -> ReplayCell:
    return ReplayCell(
        x=_require_int(data.get("x"), field="cell.x"),
        y=_require_int(data.get("y"), field="cell.y"),
        kind=_wire_kind(data),
        transport=_wire_transport(data),
        tile_type=str(data.get("tile_type") or data.get("sprite_identifier") or ""),
        rotation=int(data.get("rotation") or 0),
        layer=wire_explicit_height_layer(data),
    )


def _cell_delta_from_dict(data: dict[str, Any]) -> ReplayCellDelta:
    return ReplayCellDelta(
        x=_require_int(data.get("x"), field="cell_delta.x"),
        y=_require_int(data.get("y"), field="cell_delta.y"),
        kind=_wire_kind(data),
        transport=_wire_transport(data),
        op=str(data.get("op") or "set"),
        tile_type=str(data.get("tile_type") or data.get("sprite_identifier") or ""),
        rotation=int(data.get("rotation") or 0),
        layer=wire_explicit_height_layer(data),
    )


def _overlay_from_dict(data: dict[str, Any]) -> ReplayOverlayCell:
    return ReplayOverlayCell(
        x=_require_int(data.get("x"), field="overlay.x"),
        y=_require_int(data.get("y"), field="overlay.y"),
        kind=_wire_kind(data),
        transport=_wire_transport(data),
        tile_type=str(data.get("tile_type") or data.get("sprite_identifier") or ""),
        rotation=int(data.get("rotation") or 0),
        layer=wire_explicit_height_layer(data),
    )


def _resolved_layer_for_cell(
    *,
    kind: str,
    transport: str,
    tile_type: str,
    layer: int | None,
) -> int:
    return resolve_replay_height_layer(
        cell_kind=kind,
        transport_kind=transport,
        tile_type=tile_type,
        layer=layer,
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
            raise ReplayTimelineDeserializationError("cell list items must be objects")
        out.append(factory(dict(item)))
    return tuple(out)


def replay_map_view_to_json_dict(map_view: ReplayMapView) -> dict[str, Any]:
    return {
        "base_ref": map_view.base_ref,
        "full_cells": [
            {
                "x": c.x,
                "y": c.y,
                "kind": c.kind,
                "transport": c.transport,
                "tile_type": c.tile_type,
                "sprite_identifier": c.tile_type,
                "rotation": c.rotation,
                "layer": _resolved_layer_for_cell(
                    kind=c.kind,
                    transport=c.transport,
                    tile_type=c.tile_type,
                    layer=c.layer,
                ),
            }
            for c in map_view.full_cells
        ],
        "cell_delta": [
            {
                "x": c.x,
                "y": c.y,
                "kind": c.kind,
                "transport": c.transport,
                "op": c.op,
                "tile_type": c.tile_type,
                "sprite_identifier": c.tile_type,
                "rotation": c.rotation,
                "layer": _resolved_layer_for_cell(
                    kind=c.kind,
                    transport=c.transport,
                    tile_type=c.tile_type,
                    layer=c.layer,
                ),
            }
            for c in map_view.cell_delta
        ],
        "overlay_cells": [
            {
                "x": c.x,
                "y": c.y,
                "kind": c.kind,
                "transport": c.transport,
                "tile_type": c.tile_type,
                "sprite_identifier": c.tile_type,
                "rotation": c.rotation,
                "layer": _resolved_layer_for_cell(
                    kind=c.kind,
                    transport=c.transport,
                    tile_type=c.tile_type,
                    layer=c.layer,
                ),
            }
            for c in map_view.overlay_cells
        ],
        "annotations": [{"x": a.x, "y": a.y, "label": a.label} for a in map_view.annotations],
        "bbox": replay_bbox_to_json_dict(map_view.bbox),
    }


def replay_map_view_from_json_dict(data: object) -> ReplayMapView:
    if not isinstance(data, dict):
        raise ReplayTimelineDeserializationError("map_view must be object")
    base_ref = data.get("base_ref")
    ref: str | None
    if base_ref is None:
        ref = None
    else:
        ref = str(base_ref) or None
    return ReplayMapView(
        base_ref=ref,
        full_cells=_tuple_from_list(data.get("full_cells"), _cell_from_dict),
        cell_delta=_tuple_from_list(data.get("cell_delta"), _cell_delta_from_dict),
        overlay_cells=_tuple_from_list(data.get("overlay_cells"), _overlay_from_dict),
        annotations=_tuple_from_list(data.get("annotations"), _annotation_from_dict),
        bbox=replay_bbox_from_json_dict(data.get("bbox")),
    )


def replay_timeline_frame_to_json_dict(frame: ReplayTimelineFrame) -> dict[str, Any]:
    out: dict[str, Any] = {
        "frame_index": int(frame.frame_index),
        "phase": frame.phase.value,
        "event_type": frame.event_type.value,
        "title": str(frame.title),
        "description": str(frame.description),
        "map_view": replay_map_view_to_json_dict(frame.map_view),
        "inspector": dict(frame.inspector),
        "metrics": dict(frame.metrics),
    }
    overlay = dict(frame.cell_overlay_json or {})
    if overlay:
        out["cell_overlay_json"] = overlay
    if frame.diff:
        out["diff"] = dict(frame.diff)
    return out


def parse_replay_phase(raw: object) -> ReplayPhase:
    if not isinstance(raw, str):
        raise ReplayTimelineDeserializationError("phase must be string")
    try:
        return ReplayPhase(raw)
    except ValueError as exc:
        raise ReplayTimelineDeserializationError(f"unknown phase: {raw!r}") from exc


def parse_replay_event_type(raw: object) -> ReplayEventType:
    if not isinstance(raw, str):
        raise ReplayTimelineDeserializationError("event_type must be string")
    try:
        return ReplayEventType(raw)
    except ValueError as exc:
        raise ReplayTimelineDeserializationError(f"unknown event_type: {raw!r}") from exc


def replay_timeline_frame_from_json_dict(data: Mapping[str, Any]) -> ReplayTimelineFrame:
    if "map_view" not in data:
        raise ReplayTimelineDeserializationError("map_view is required")
    raw_diff = data.get("diff")
    diff_out: dict[str, Any] | None = None
    if isinstance(raw_diff, dict) and raw_diff:
        diff_out = dict(raw_diff)
    return ReplayTimelineFrame(
        frame_index=_require_int(data.get("frame_index"), field="frame_index"),
        phase=parse_replay_phase(data.get("phase")),
        event_type=parse_replay_event_type(data.get("event_type")),
        title=str(data.get("title") or ""),
        description=str(data.get("description") or ""),
        map_view=replay_map_view_from_json_dict(data.get("map_view")),
        inspector=_mapping(data.get("inspector")),
        metrics=_mapping(data.get("metrics")),
        cell_overlay_json=_mapping(data.get("cell_overlay_json")),
        diff=diff_out,
    )


def replay_timeline_frame_json_round_trip(frame: ReplayTimelineFrame) -> ReplayTimelineFrame:
    """Serialize to JSON text and back (contract helper for tests)."""
    payload = replay_timeline_frame_to_json_dict(frame)
    text = json.dumps(payload, default=str)
    restored = json.loads(text)
    if not isinstance(restored, dict):
        raise ReplayTimelineDeserializationError("round-trip did not yield object")
    return replay_timeline_frame_from_json_dict(restored)
