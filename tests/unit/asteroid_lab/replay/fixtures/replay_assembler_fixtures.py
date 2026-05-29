"""Fixtures for central solver runtime replay assembler tests."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayMapView
from django_apps.asteroid_lab.replay.timeline_serialization import replay_map_view_from_json_dict
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)


def reconstruction_complete_lab_frame_dict_for_golden() -> dict[str, object]:
    """Minimal renderable reconstruction.completed wire for golden 5×5 map."""
    complete = golden_5x5_complete_map()
    rows = [
        {
            "x": x,
            "y": y,
            "kind": "asteroid_shape_field",
            "transport": "",
            "rotation": 0,
        }
        for x, y in sorted(complete.field_cells)
    ]
    xs = [int(r["x"]) for r in rows]
    ys = [int(r["y"]) for r in rows]
    return {
        "frame_index": 0,
        "event_type": ReplayEventType.RECONSTRUCTION_COMPLETED.value,
        "phase": "reconstruction",
        "map_view": {
            "full_cells": rows,
            "overlay_cells": [],
            "cell_delta": [],
            "annotations": [],
            "bbox": {
                "min_x": min(xs),
                "min_y": min(ys),
                "max_x": max(xs),
                "max_y": max(ys),
            },
        },
        "metrics": {},
    }


def exterior_plan_wire_for_golden() -> dict[str, object]:
    metrics = exterior_connector_plan_to_metrics_dict(minimal_l2_plan_for_golden())
    wire = metrics["exterior_connector_plan"]
    if not isinstance(wire, dict):
        msg = "exterior_connector_plan wire must be a dict"
        raise TypeError(msg)
    return wire


def renderable_base_map_view_for_golden() -> ReplayMapView:
    raw_map_view = reconstruction_complete_lab_frame_dict_for_golden()["map_view"]
    if not isinstance(raw_map_view, dict):
        msg = "map_view must be a dict"
        raise TypeError(msg)
    return replay_map_view_from_json_dict(raw_map_view)


def golden_complete_map() -> ReconstructionCompleteMap:
    return golden_5x5_complete_map()
