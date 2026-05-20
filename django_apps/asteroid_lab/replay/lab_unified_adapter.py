"""Lab ReplayFrame / SnapshotEventDTO → UnifiedReplayFrame (Phase 9B; output-only)."""

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
from django_apps.asteroid_lab.replay.unified_dtos import (
    ReplayBBox,
    ReplayCell,
    ReplayMapView,
    ReplayOverlayCell,
    UnifiedReplayFrame,
    replay_map_view_is_renderable,
)
from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.unified_event_coverage import SUPPORTED_BY_9B_LAB_ADAPTER
from django_apps.asteroid_lab.services.dto import ReplayFrameRowDTO, SnapshotEventDTO
from django_apps.asteroid_lab.snapshots.equipment_bundles import (
    cell_overlay_json_for_bundle_highlight,
    equipment_bundle_overlay_from_rows,
)

LAB_PHASE_DECODE = "decode"
LAB_PHASE_RECONSTRUCTION = "reconstruction"
LAB_PHASE_LAYOUT_CLEANUP = "layout_cleanup"

_LAB_PHASES_9B = frozenset({LAB_PHASE_DECODE, LAB_PHASE_RECONSTRUCTION, LAB_PHASE_LAYOUT_CLEANUP})

LAB_EVENT_TYPE_TO_UNIFIED: dict[str, ReplayEventType] = {
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

LAB_PHASE_TO_UNIFIED: dict[str, ReplayPhase] = {
    LAB_PHASE_DECODE: ReplayPhase.DECODE,
    LAB_PHASE_RECONSTRUCTION: ReplayPhase.RECONSTRUCTION,
    LAB_PHASE_LAYOUT_CLEANUP: ReplayPhase.RECONSTRUCTION,
}


class LabUnifiedAdapterError(ValueError):
    """Raised when a Lab replay frame cannot be conservatively wrapped for 9B."""


def _lab_phase_to_unified(phase: str) -> ReplayPhase:
    try:
        return LAB_PHASE_TO_UNIFIED[phase]
    except KeyError as exc:
        msg = f"Lab phase not supported by 9B adapter: {phase!r}"
        raise LabUnifiedAdapterError(msg) from exc


def _lab_event_type_to_unified(event_type: str) -> ReplayEventType:
    unified = LAB_EVENT_TYPE_TO_UNIFIED.get(event_type)
    if unified is None:
        msg = f"Lab event_type not supported by 9B adapter: {event_type!r}"
        raise LabUnifiedAdapterError(msg)
    if unified not in SUPPORTED_BY_9B_LAB_ADAPTER:
        msg = f"Mapped unified event_type not in 9B output set: {unified!r}"
        raise LabUnifiedAdapterError(msg)
    return unified


def _cell_from_row(row: Mapping[str, Any]) -> ReplayCell:
    return ReplayCell(
        x=int(row["x"]),
        y=int(row["y"]),
        kind=str(row.get("cell_kind") or row.get("kind") or ""),
        transport=str(row.get("transport_kind") or row.get("transport") or ""),
        tile_type=str(row.get("tile_type") or row.get("sprite_identifier") or ""),
        rotation=int(row.get("rotation") or 0),
    )


def _overlay_from_row(row: Mapping[str, Any]) -> ReplayOverlayCell:
    return ReplayOverlayCell(
        x=int(row["x"]),
        y=int(row["y"]),
        kind=str(row.get("cell_kind") or row.get("kind") or ""),
        transport=str(row.get("transport_kind") or row.get("transport") or ""),
        tile_type=str(row.get("tile_type") or row.get("sprite_identifier") or ""),
        rotation=int(row.get("rotation") or 0),
    )


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


def _build_map_view(
    *,
    full_map: list[Any],
    cell_overlay_json: Mapping[str, Any],
) -> ReplayMapView:
    full_cells = _rows_to_full_cells(full_map)
    overlay_cells = _overlay_rows_from_json(cell_overlay_json)
    bbox = _bbox_from_cells(full_cells, overlay_cells)
    map_view = ReplayMapView(
        bbox=bbox,
        full_cells=full_cells,
        overlay_cells=overlay_cells,
    )
    if not replay_map_view_is_renderable(map_view):
        msg = "Lab frame has no renderable map_view (empty full_map and no overlay/base_ref)"
        raise LabUnifiedAdapterError(msg)
    return map_view


def _cell_overlay_json_for_unified_lab_frame(
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
    for cell in (*map_view.full_cells, *map_view.overlay_cells):
        key = (int(cell.x), int(cell.y))
        if key in seen:
            continue
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


def lab_snapshot_event_to_unified(
    event: SnapshotEventDTO,
    *,
    frame_index: int,
) -> UnifiedReplayFrame:
    """Wrap one in-memory Lab snapshot event (does not mutate ``event``)."""

    phase = str(event.phase)
    event_type = str(event.event_type)
    _lab_phase_to_unified(phase)
    unified_event = _lab_event_type_to_unified(event_type)
    map_view = _build_map_view(
        full_map=list(event.full_map),
        cell_overlay_json=dict(event.cell_overlay_json or {}),
    )
    overlay_json = dict(event.cell_overlay_json or {})
    return UnifiedReplayFrame(
        frame_index=int(frame_index),
        phase=_lab_phase_to_unified(phase),
        event_type=unified_event,
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
        cell_overlay_json=_cell_overlay_json_for_unified_lab_frame(
            overlay_json,
            full_map=list(event.full_map),
            map_view=map_view,
        ),
    )


def _snapshot_fields_from_payload(
    payload: Mapping[str, Any],
) -> tuple[str, str, str, str, list[Any]]:
    phase = str(payload.get("phase") or "")
    event_type = str(payload.get("event_type") or "")
    if not event_type:
        msg = "frame_payload missing event_type"
        raise LabUnifiedAdapterError(msg)
    event_key = str(payload.get("event_key") or "")
    phase_step = str(payload.get("phase_step") or "")
    full_map = payload.get("full_map")
    if not isinstance(full_map, list):
        full_map = []
    return phase, event_type, event_key, phase_step, full_map


def lab_replay_row_to_unified(row: ReplayFrameRowDTO) -> UnifiedReplayFrame:
    """Wrap one persisted Lab ``ReplayFrame`` row (does not mutate ``row``)."""

    payload = row.frame_payload
    if not isinstance(payload, dict):
        msg = "ReplayFrameRowDTO.frame_payload must be a dict"
        raise LabUnifiedAdapterError(msg)
    phase, event_type, event_key, phase_step, full_map = _snapshot_fields_from_payload(payload)
    _lab_phase_to_unified(phase)
    unified_event = _lab_event_type_to_unified(event_type)
    overlay_json = row.cell_overlay_json if isinstance(row.cell_overlay_json, dict) else {}
    if not overlay_json and isinstance(payload.get("cell_overlay_json"), dict):
        overlay_json = dict(payload["cell_overlay_json"])
    map_view = _build_map_view(full_map=full_map, cell_overlay_json=overlay_json)
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
    return UnifiedReplayFrame(
        frame_index=int(row.frame_index),
        phase=_lab_phase_to_unified(phase),
        event_type=unified_event,
        title=str(row.title),
        description=str(row.description),
        map_view=map_view,
        inspector=inspector,
        metrics=metrics,
        cell_overlay_json=_cell_overlay_json_for_unified_lab_frame(
            overlay_json,
            full_map=full_map,
            map_view=map_view,
        ),
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
