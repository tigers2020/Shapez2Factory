"""Layer 02 solver timeline frame builder (append-stack; output-only)."""

from __future__ import annotations

import copy
from typing import Any

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
    METRICS_KEY,
    OVERLAY_ROLE,
    _connector_coord_keys,
    _overlay_without_connector_coord_duplicates,
    _planned_connectors,
)
from django_apps.asteroid_lab.services.lab_timeline_rim_enrichment import frame_has_renderable_map

LAYER02_EVENT_TYPE = ReplayEventType.EXTERIOR_TRANSPORT_COMPLETED.value
LAYER02_INSPECTOR_STEP = "layer_02_exterior_transport"


def resolve_l2_complete_frame_index(
    frames: list[dict[str, Any]],
    *,
    explicit_index: int | None = None,
) -> int | None:
    """Index of first frame that should show L2 overlay; None when L2 is not on the timeline."""

    if explicit_index is not None and explicit_index >= 0:
        return explicit_index
    for index, frame in enumerate(frames):
        if frame.get("event_type") == LAYER02_EVENT_TYPE:
            return index
    return None


def find_reconstruction_complete_source_frame(
    frames: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Last renderable ``reconstruction.completed`` frame (L1 map base for L2 append)."""

    for frame in reversed(frames):
        if frame.get("event_type") != ReplayEventType.RECONSTRUCTION_COMPLETED.value:
            continue
        if frame_has_renderable_map(frame):
            return frame
    return None


def _display_rows_from_complete_map(
    complete_map: ReconstructionCompleteMap,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cell in complete_map.cells:
        rows.append(_decoded_cell_to_row(cell))
    return rows


def _decoded_cell_to_row(cell: DecodedCellDTO) -> dict[str, Any]:
    return {
        "x": int(cell.x),
        "y": int(cell.y),
        "cell_kind": str(cell.cell_kind),
        "transport_kind": str(cell.transport_kind or ""),
        "rotation": int(cell.rotation),
        "tile_type": str(cell.tile_type or ""),
    }


def _bbox_from_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    xs = [int(r["x"]) for r in rows if "x" in r]
    ys = [int(r["y"]) for r in rows if "y" in r]
    if not xs:
        return {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0}
    return {"min_x": min(xs), "min_y": min(ys), "max_x": max(xs), "max_y": max(ys)}


def build_layer02_timeline_frame_dict(
    *,
    plan_wire: dict[str, object],
    source_frame: dict[str, Any] | None,
    complete_map: ReconstructionCompleteMap | None,
) -> dict[str, Any]:
    """One append-stack milestone: L1 full map + L2 planned connector overlay only."""

    planned_overlay = _planned_connectors(plan_wire)
    if source_frame is not None:
        base = copy.deepcopy(source_frame)
        map_view = copy.deepcopy(base.get("map_view") or {})
        full_cells = list(map_view.get("full_cells") or [])
        if not full_cells and complete_map is not None:
            full_cells = _display_rows_from_complete_map(complete_map)
            map_view["full_cells"] = full_cells
            map_view["bbox"] = _bbox_from_rows(full_cells)
    elif complete_map is not None:
        full_cells = _display_rows_from_complete_map(complete_map)
        map_view = {
            "base_ref": None,
            "full_cells": full_cells,
            "cell_delta": [],
            "overlay_cells": [],
            "annotations": [],
            "bbox": _bbox_from_rows(full_cells),
        }
        base = {}
    else:
        msg = "build_layer02_timeline_frame_dict requires source_frame or complete_map"
        raise ValueError(msg)

    connector_coords = _connector_coord_keys(plan_wire)
    overlay = [
        row
        for row in (map_view.get("overlay_cells") or [])
        if not (isinstance(row, dict) and row.get("overlay_role") == OVERLAY_ROLE)
    ]
    overlay = _overlay_without_connector_coord_duplicates(overlay, connector_coords)
    overlay.extend(planned_overlay)
    map_view["overlay_cells"] = overlay

    metrics = dict(base.get("metrics") or {})
    metrics[METRICS_KEY] = plan_wire

    planned_count = plan_wire.get("planned_connector_count")
    if planned_count is None:
        planned_count = len(planned_overlay)

    return {
        "frame_index": 0,
        "phase": "reconstruction",
        "event_type": LAYER02_EVENT_TYPE,
        "title": "Exterior transport complete",
        "description": f"Planned {planned_count} exterior connector(s)",
        "map_view": map_view,
        "inspector": {
            "lab_phase": "reconstruction",
            "lab_phase_step": LAYER02_INSPECTOR_STEP,
            "lab_event_type": LAYER02_EVENT_TYPE,
            "event_key": "layer_02_exterior_transport_complete",
        },
        "metrics": metrics,
    }


def build_layer02_runtime_replay_frames(
    *,
    plan_wire: dict[str, object],
    lab_frames_before_append: list[dict[str, Any]],
    complete_map: ReconstructionCompleteMap,
) -> list[dict[str, Any]]:
    """Persisted solver runtime frames: single L2 append milestone."""

    source = find_reconstruction_complete_source_frame(lab_frames_before_append)
    frame_dict = build_layer02_timeline_frame_dict(
        plan_wire=plan_wire,
        source_frame=source,
        complete_map=complete_map if source is None else None,
    )
    return [frame_dict]


__all__ = [
    "LAYER02_EVENT_TYPE",
    "LAYER02_INSPECTOR_STEP",
    "build_layer02_runtime_replay_frames",
    "build_layer02_timeline_frame_dict",
    "find_reconstruction_complete_source_frame",
    "resolve_l2_complete_frame_index",
]
