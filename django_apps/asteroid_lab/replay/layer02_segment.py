"""Layer 02 exterior transport runtime replay segment (projection only)."""

from __future__ import annotations

import copy
from typing import Any

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayMapView, ReplayTimelineFrame
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_map_view_from_json_dict,
    replay_timeline_frame_from_json_dict,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
    METRICS_KEY,
    OVERLAY_ROLE,
    _connector_coord_keys,
    _overlay_without_connector_coord_duplicates,
    planned_connector_overlays_from_wire,
)

LAYER02_EVENT_TYPE = ReplayEventType.EXTERIOR_TRANSPORT_COMPLETED
LAYER02_INSPECTOR_STEP = "layer_02_exterior_transport"


def map_view_from_complete_map(complete_map: ReconstructionCompleteMap) -> ReplayMapView:
    rows = _display_rows_from_complete_map(complete_map)
    return replay_map_view_from_json_dict(
        {
            "base_ref": None,
            "full_cells": rows,
            "cell_delta": [],
            "overlay_cells": [],
            "annotations": [],
            "bbox": _bbox_from_rows(rows),
        }
    )


def _display_rows_from_complete_map(
    complete_map: ReconstructionCompleteMap,
) -> list[dict[str, Any]]:
    if complete_map.cells:
        return [_decoded_cell_to_row(cell) for cell in complete_map.cells]
    return [
        {
            "x": int(x),
            "y": int(y),
            "kind": "asteroid_shape_field",
            "transport": "",
            "rotation": 0,
            "tile_type": "",
        }
        for x, y in sorted(complete_map.field_cells)
    ]


def _decoded_cell_to_row(cell: DecodedCellDTO) -> dict[str, Any]:
    return {
        "x": int(cell.x),
        "y": int(cell.y),
        "kind": str(cell.cell_kind),
        "transport": str(cell.transport_kind or ""),
        "rotation": int(cell.rotation),
        "tile_type": str(cell.tile_type or ""),
    }


def _bbox_from_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    xs = [int(r["x"]) for r in rows if "x" in r]
    ys = [int(r["y"]) for r in rows if "y" in r]
    if not xs:
        return {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0}
    return {"min_x": min(xs), "min_y": min(ys), "max_x": max(xs), "max_y": max(ys)}


def build_layer02_timeline_frame_wire_dict(
    *,
    plan_wire: dict[str, object],
    source_frame: dict[str, Any] | None,
    complete_map: ReconstructionCompleteMap | None,
) -> dict[str, Any]:
    """Wire dict for one L2 append milestone (L1 full map + connector overlay)."""

    planned_overlay = planned_connector_overlays_from_wire(plan_wire)
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
        msg = "build_layer02_timeline_frame_wire_dict requires source_frame or complete_map"
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
    required_planned = plan_wire.get("required_planned_count", planned_count)
    spare_planned = plan_wire.get("spare_planned_count", 0)

    return {
        "frame_index": 0,
        "phase": ReplayPhase.RECONSTRUCTION.value,
        "event_type": LAYER02_EVENT_TYPE.value,
        "title": "Exterior transport complete",
        "description": (
            f"Planned {planned_count} exterior connector(s) "
            f"({required_planned} required, {spare_planned} spare)"
        ),
        "map_view": map_view,
        "inspector": {
            "lab_phase": "reconstruction",
            "lab_phase_step": LAYER02_INSPECTOR_STEP,
            "lab_event_type": LAYER02_EVENT_TYPE.value,
            "event_key": "layer_02_exterior_transport_complete",
        },
        "metrics": metrics,
    }


def build_layer02_exterior_transport_frame(
    *,
    plan_wire: dict[str, object],
    source_frame: dict[str, Any] | None,
    complete_map: ReconstructionCompleteMap | None,
) -> ReplayTimelineFrame:
    wire = build_layer02_timeline_frame_wire_dict(
        plan_wire=plan_wire,
        source_frame=source_frame,
        complete_map=complete_map,
    )
    return replay_timeline_frame_from_json_dict(wire)


__all__ = [
    "LAYER02_EVENT_TYPE",
    "LAYER02_INSPECTOR_STEP",
    "build_layer02_exterior_transport_frame",
    "build_layer02_timeline_frame_wire_dict",
    "map_view_from_complete_map",
]
