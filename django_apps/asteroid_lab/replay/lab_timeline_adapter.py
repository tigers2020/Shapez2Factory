"""Lab ReplayFrame / SnapshotEventDTO → ReplayTimelineFrame (Phase 9B; output-only)."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_DECODE_NORMALIZED,
    EVENT_TYPE_DECODE_RAW_LOADED,
    EVENT_TYPE_RECONSTRUCTION_BEGIN,
    EVENT_TYPE_RECONSTRUCTION_CLEAR_OLD_LAYOUT,
    EVENT_TYPE_RECONSTRUCTION_EXTERNAL_FLOOD_FILL,
    EVENT_TYPE_RECONSTRUCTION_INTERIOR_PATCH_MARKED,
    EVENT_TYPE_RECONSTRUCTION_INTERNAL_VOID_DETECTED,
    EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
    EVENT_TYPE_RECONSTRUCTION_MINEABLE_FINALIZED,
    EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED,
    EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTENSION,
    EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTRACTOR,
    EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT,
    EVENT_TYPE_REPLAY_SNAPSHOT_RECONSTRUCTION,
)
from django_apps.asteroid_lab.replay.map_height_layer import wire_explicit_height_layer
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.replay_event_coverage import SUPPORTED_BY_9B_LAB_ADAPTER
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayBBox,
    ReplayCell,
    ReplayMapView,
    ReplayOverlayCell,
    ReplayTimelineFrame,
    replay_map_view_is_renderable,
)
from django_apps.asteroid_lab.replay.timeline_serialization import replay_overlay_cell_from_wire
from django_apps.asteroid_lab.services.dto import ReplayFrameRowDTO, SnapshotEventDTO
from django_apps.asteroid_lab.snapshots.equipment_bundles import (
    cell_overlay_json_for_bundle_highlight,
    equipment_bundle_overlay_from_rows,
)

LAB_PHASE_DECODE = "decode"
LAB_PHASE_RECONSTRUCTION = "reconstruction"
LAB_PHASE_LAYOUT_CLEANUP = "layout_cleanup"

_LAB_PHASES_9B = frozenset({LAB_PHASE_DECODE, LAB_PHASE_RECONSTRUCTION, LAB_PHASE_LAYOUT_CLEANUP})

LAB_EVENT_TYPE_TO_TIMELINE: dict[str, ReplayEventType] = {
    EVENT_TYPE_DECODE_RAW_LOADED: ReplayEventType.DECODE_STARTED,
    EVENT_TYPE_DECODE_NORMALIZED: ReplayEventType.DECODE_COMPLETED,
    EVENT_TYPE_RECONSTRUCTION_BEGIN: ReplayEventType.RECONSTRUCTION_STARTED,
    EVENT_TYPE_RECONSTRUCTION_CLEAR_OLD_LAYOUT: ReplayEventType.RECONSTRUCTION_STARTED,
    EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED: ReplayEventType.RECONSTRUCTION_STARTED,
    EVENT_TYPE_RECONSTRUCTION_EXTERNAL_FLOOD_FILL: ReplayEventType.RECONSTRUCTION_STARTED,
    EVENT_TYPE_RECONSTRUCTION_INTERNAL_VOID_DETECTED: ReplayEventType.RECONSTRUCTION_STARTED,
    EVENT_TYPE_RECONSTRUCTION_INTERIOR_PATCH_MARKED: ReplayEventType.RECONSTRUCTION_STARTED,
    EVENT_TYPE_RECONSTRUCTION_MINEABLE_FINALIZED: ReplayEventType.RECONSTRUCTION_STARTED,
    EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE: ReplayEventType.RECONSTRUCTION_COMPLETED,
    EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT: ReplayEventType.RECONSTRUCTION_STARTED,
    EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTRACTOR: ReplayEventType.RECONSTRUCTION_STARTED,
    EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTENSION: ReplayEventType.RECONSTRUCTION_STARTED,
    EVENT_TYPE_REPLAY_SNAPSHOT_RECONSTRUCTION: ReplayEventType.RECONSTRUCTION_STARTED,
}

LAB_PHASE_TO_TIMELINE: dict[str, ReplayPhase] = {
    LAB_PHASE_DECODE: ReplayPhase.DECODE,
    LAB_PHASE_RECONSTRUCTION: ReplayPhase.RECONSTRUCTION,
    LAB_PHASE_LAYOUT_CLEANUP: ReplayPhase.RECONSTRUCTION,
}


class LabTimelineAdapterError(ValueError):
    """Raised when a Lab replay frame cannot be conservatively wrapped for 9B."""


def _lab_phase_to_timeline(phase: str) -> ReplayPhase:
    try:
        return LAB_PHASE_TO_TIMELINE[phase]
    except KeyError as exc:
        msg = f"Lab phase not supported by 9B adapter: {phase!r}"
        raise LabTimelineAdapterError(msg) from exc


def _lab_event_type_to_timeline(event_type: str) -> ReplayEventType:
    timeline_event = LAB_EVENT_TYPE_TO_TIMELINE.get(event_type)
    if timeline_event is None:
        msg = f"Lab event_type not supported by 9B adapter: {event_type!r}"
        raise LabTimelineAdapterError(msg)
    if timeline_event not in SUPPORTED_BY_9B_LAB_ADAPTER:
        msg = f"Mapped timeline event_type not in 9B output set: {timeline_event!r}"
        raise LabTimelineAdapterError(msg)
    return timeline_event


def _cell_from_row(row: Mapping[str, Any]) -> ReplayCell:
    return ReplayCell(
        x=int(row["x"]),
        y=int(row["y"]),
        kind=str(row.get("cell_kind") or row.get("kind") or ""),
        transport=str(row.get("transport_kind") or row.get("transport") or ""),
        tile_type=str(row.get("tile_type") or row.get("sprite_identifier") or ""),
        rotation=int(row.get("rotation") or 0),
        layer=wire_explicit_height_layer(row),
    )


def _overlay_from_row(row: Mapping[str, Any]) -> ReplayOverlayCell:
    if not isinstance(row, dict) or "x" not in row or "y" not in row:
        msg = "overlay row must be a dict with x and y"
        raise LabTimelineAdapterError(msg)
    return replay_overlay_cell_from_wire(row)


def _bbox_from_cells(
    full_cells: tuple[ReplayCell, ...],
    overlay_cells: tuple[ReplayOverlayCell, ...],
) -> ReplayBBox:
    xs: list[int] = []
    ys: list[int] = []
    for c in full_cells:
        xs.append(c.x)
        ys.append(c.y)
    for o in overlay_cells:
        xs.append(o.x)
        ys.append(o.y)
    if not xs:
        return ReplayBBox(min_x=0, min_y=0, max_x=0, max_y=0)
    return ReplayBBox(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys))


def _rows_to_full_cells(rows: list[Any]) -> tuple[ReplayCell, ...]:
    out: list[ReplayCell] = []
    for raw in rows:
        if not isinstance(raw, dict) or "x" not in raw or "y" not in raw:
            continue
        out.append(_cell_from_row(raw))
    return tuple(out)


def _overlay_rows_from_json(overlay_json: Mapping[str, Any]) -> tuple[ReplayOverlayCell, ...]:
    cells = overlay_json.get("cells")
    if not isinstance(cells, list):
        return ()
    out: list[ReplayOverlayCell] = []
    for raw in cells:
        if not isinstance(raw, dict) or "x" not in raw or "y" not in raw:
            continue
        out.append(_overlay_from_row(raw))
    return tuple(out)


def _normalize_lab_diff(diff: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(diff, dict):
        return None
    added = diff.get("added")
    removed = diff.get("removed")
    changed = diff.get("changed")
    has_added = isinstance(added, list) and bool(added)
    has_removed = isinstance(removed, list) and bool(removed)
    has_changed = isinstance(changed, list) and bool(changed)
    if not (has_added or has_removed or has_changed):
        return None
    return {
        "added": list(added) if isinstance(added, list) else [],
        "removed": list(removed) if isinstance(removed, list) else [],
        "changed": list(changed) if isinstance(changed, list) else [],
    }


def _trace_overlay_cells_from_diff(diff: Mapping[str, Any] | None) -> tuple[ReplayOverlayCell, ...]:
    if not isinstance(diff, dict):
        return ()
    added = diff.get("added")
    if not isinstance(added, list):
        return ()
    out: list[ReplayOverlayCell] = []
    for raw in added:
        if not isinstance(raw, dict) or "x" not in raw or "y" not in raw:
            continue
        if not raw.get("_replay_trace"):
            continue
        out.append(_overlay_from_row(raw))
    return tuple(out)


def _merge_overlay_cells(
    persisted: tuple[ReplayOverlayCell, ...],
    trace: tuple[ReplayOverlayCell, ...],
) -> tuple[ReplayOverlayCell, ...]:
    """Trace highlights win on duplicate ``(x, y)``."""

    by_xy: dict[tuple[int, int], ReplayOverlayCell] = {(o.x, o.y): o for o in persisted}
    for cell in trace:
        by_xy[(cell.x, cell.y)] = cell
    if not by_xy:
        return ()
    return tuple(by_xy[key] for key in sorted(by_xy))


def _build_map_view(
    *,
    full_map: list[Any],
    cell_overlay_json: Mapping[str, Any],
    diff: Mapping[str, Any] | None = None,
) -> ReplayMapView:
    full_cells = _rows_to_full_cells(full_map)
    persisted_overlay = _overlay_rows_from_json(cell_overlay_json)
    trace_overlay = _trace_overlay_cells_from_diff(diff)
    overlay_cells = _merge_overlay_cells(persisted_overlay, trace_overlay)
    bbox = _bbox_from_cells(full_cells, overlay_cells)
    map_view = ReplayMapView(
        bbox=bbox,
        full_cells=full_cells,
        overlay_cells=overlay_cells,
    )
    if not replay_map_view_is_renderable(map_view):
        msg = "Lab frame has no renderable map_view (empty full_map and no overlay/base_ref)"
        raise LabTimelineAdapterError(msg)
    return map_view


def _cell_overlay_json_for_timeline_lab_frame(
    overlay_json: Mapping[str, Any],
    *,
    full_map: list[Any],
    map_view: ReplayMapView,
) -> dict[str, Any]:
    """Wire overlay for bundle highlight: persisted bundles, else rebuild from map cells."""

    overlay = cell_overlay_json_for_bundle_highlight(overlay_json, full_map=full_map)
    if overlay.get("equipment_bundles"):
        return overlay
    rows: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()

    def _append_map_cell(cell: ReplayCell | ReplayOverlayCell) -> None:
        key = (int(cell.x), int(cell.y))
        if key in seen:
            return
        seen.add(key)
        rows.append(
            {
                "x": key[0],
                "y": key[1],
                "cell_kind": str(cell.kind),
                "transport_kind": str(cell.transport),
                "rotation": int(cell.rotation),
                "tile_type": str(cell.tile_type),
            }
        )

    for full_cell in map_view.full_cells:
        _append_map_cell(full_cell)
    for overlay_cell in map_view.overlay_cells:
        _append_map_cell(overlay_cell)
    return equipment_bundle_overlay_from_rows(rows) or overlay


def _inspector_from_lab(
    *,
    event_key: str,
    lab_phase: str,
    lab_phase_step: str,
    lab_event_type: str,
) -> dict[str, Any]:
    return {
        "event_key": event_key,
        "lab_phase": lab_phase,
        "lab_phase_step": lab_phase_step,
        "lab_event_type": lab_event_type,
    }


def lab_snapshot_event_to_timeline_frame(
    event: SnapshotEventDTO,
    *,
    frame_index: int,
) -> ReplayTimelineFrame:
    """Wrap one in-memory Lab snapshot event (does not mutate ``event``)."""

    phase = str(event.phase)
    event_type = str(event.event_type)
    _lab_phase_to_timeline(phase)
    timeline_event = _lab_event_type_to_timeline(event_type)
    diff_norm = _normalize_lab_diff(event.diff)
    map_view = _build_map_view(
        full_map=list(event.full_map),
        cell_overlay_json=dict(event.cell_overlay_json or {}),
        diff=diff_norm,
    )
    overlay_json = dict(event.cell_overlay_json or {})
    return ReplayTimelineFrame(
        frame_index=int(frame_index),
        phase=_lab_phase_to_timeline(phase),
        event_type=timeline_event,
        title=str(event.title),
        description=str(event.description),
        map_view=map_view,
        inspector=_inspector_from_lab(
            event_key=str(event.event_key),
            lab_phase=phase,
            lab_phase_step=str(event.phase_step),
            lab_event_type=event_type,
        ),
        metrics=dict(event.metrics_json or {}),
        cell_overlay_json=_cell_overlay_json_for_timeline_lab_frame(
            overlay_json,
            full_map=list(event.full_map),
            map_view=map_view,
        ),
        diff=diff_norm,
    )


def _snapshot_fields_from_payload(
    payload: Mapping[str, Any],
) -> tuple[str, str, str, str, list[Any]]:
    phase = str(payload.get("phase") or "")
    event_type = str(payload.get("event_type") or "")
    if not event_type:
        msg = "frame_payload missing event_type"
        raise LabTimelineAdapterError(msg)
    event_key = str(payload.get("event_key") or "")
    phase_step = str(payload.get("phase_step") or "")
    full_map = payload.get("full_map")
    if not isinstance(full_map, list):
        full_map = []
    return phase, event_type, event_key, phase_step, full_map


def lab_replay_row_to_timeline_frame(row: ReplayFrameRowDTO) -> ReplayTimelineFrame:
    """Wrap one persisted Lab ``ReplayFrame`` row (does not mutate ``row``)."""

    payload = row.frame_payload
    if not isinstance(payload, dict):
        msg = "ReplayFrameRowDTO.frame_payload must be a dict"
        raise LabTimelineAdapterError(msg)
    phase, event_type, event_key, phase_step, full_map = _snapshot_fields_from_payload(payload)
    _lab_phase_to_timeline(phase)
    timeline_event = _lab_event_type_to_timeline(event_type)
    overlay_json = row.cell_overlay_json if isinstance(row.cell_overlay_json, dict) else {}
    if not overlay_json and isinstance(payload.get("cell_overlay_json"), dict):
        overlay_json = dict(payload["cell_overlay_json"])
    raw_diff = payload.get("diff")
    diff_norm = _normalize_lab_diff(raw_diff if isinstance(raw_diff, dict) else None)
    map_view = _build_map_view(
        full_map=full_map,
        cell_overlay_json=overlay_json,
        diff=diff_norm,
    )
    metrics: dict[str, Any] = {}
    if isinstance(row.metric_snapshot_json, dict):
        metrics.update(row.metric_snapshot_json)
    payload_metrics = payload.get("metrics_json")
    if isinstance(payload_metrics, dict):
        metrics.update(payload_metrics)
    inspector = _inspector_from_lab(
        event_key=event_key,
        lab_phase=phase,
        lab_phase_step=phase_step,
        lab_event_type=event_type,
    )
    inspector["replay_frame_id"] = int(row.id)
    return ReplayTimelineFrame(
        frame_index=int(row.frame_index),
        phase=_lab_phase_to_timeline(phase),
        event_type=timeline_event,
        title=str(row.title),
        description=str(row.description),
        map_view=map_view,
        inspector=inspector,
        metrics=metrics,
        cell_overlay_json=_cell_overlay_json_for_timeline_lab_frame(
            overlay_json,
            full_map=full_map,
            map_view=map_view,
        ),
        diff=diff_norm,
    )


def lab_snapshot_event_payload_copy(event: SnapshotEventDTO) -> dict[str, Any]:
    """Deep copy of snapshot fields for immutability tests (not part of public API)."""

    return deepcopy(
        {
            "event_key": event.event_key,
            "phase": event.phase,
            "phase_step": event.phase_step,
            "event_type": event.event_type,
            "full_map": event.full_map,
            "cell_overlay_json": event.cell_overlay_json,
            "metrics_json": event.metrics_json,
        }
    )
