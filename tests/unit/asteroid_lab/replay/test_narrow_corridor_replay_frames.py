"""Sequence 10A backend replay frame contract for narrow-corridor fixtures."""

from __future__ import annotations

import hashlib
import json

from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_BEGIN,
    EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_COMPLETE,
)
from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
    build_solver_runtime_replay_frames,
)
from django_apps.asteroid_lab.replay.timeline_dtos import replay_map_view_is_renderable
from django_apps.asteroid_lab.replay.timeline_serialization import replay_map_view_from_json_dict
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.candidate_gen import (
    generate_candidates,
)
from tests.unit.asteroid_lab.layers.fixtures.narrow_corridor_maps import (
    s3_corridor_sharing_catalog,
    s3_corridor_sharing_complete_map,
    s3_corridor_sharing_exterior_plan,
)


def _reconstruction_lab_frame() -> dict[str, object]:
    complete = s3_corridor_sharing_complete_map()
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
        "event_type": "reconstruction.completed",
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


def _exterior_plan_wire() -> dict[str, object]:
    metrics = exterior_connector_plan_to_metrics_dict(s3_corridor_sharing_exterior_plan())
    wire = metrics["exterior_connector_plan"]
    if not isinstance(wire, dict):
        msg = "exterior_connector_plan wire must be a dict"
        raise TypeError(msg)
    return wire


def _assemble_frames() -> list[dict[str, object]]:
    layer03 = generate_candidates(
        complete_map=s3_corridor_sharing_complete_map(),
        exterior_plan=s3_corridor_sharing_exterior_plan(),
        genetic_sample_seeds=s3_corridor_sharing_catalog(),
    )
    return build_solver_runtime_replay_frames(
        complete_map=s3_corridor_sharing_complete_map(),
        lab_frames_before_append=[_reconstruction_lab_frame()],
        exterior_plan_wire=_exterior_plan_wire(),
        layer03=layer03,
        layer04=None,
    )


def _overlay_fingerprint(frames: list[dict[str, object]]) -> str:
    complete = next(
        f for f in frames if f.get("event_type") == EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_COMPLETE
    )
    overlay = complete.get("map_view", {}).get("overlay_cells", [])
    payload = json.dumps(overlay, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_narrow_corridor_replay_event_order_is_stable() -> None:
    frames = _assemble_frames()
    types = [str(f.get("event_type")) for f in frames]
    assert types.index("exterior_transport.completed") < types.index(
        EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_BEGIN
    )
    assert types.index(EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_BEGIN) < types.index(
        EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_COMPLETE
    )
    assert _assemble_frames()[0]["event_type"] == frames[0]["event_type"]
    assert [f["event_type"] for f in _assemble_frames()] == types


def test_narrow_corridor_l3_complete_overlay_is_stable() -> None:
    first = _assemble_frames()
    second = _assemble_frames()
    assert _overlay_fingerprint(first) == _overlay_fingerprint(second)
    complete = next(
        f for f in first if f.get("event_type") == EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_COMPLETE
    )
    map_view = replay_map_view_from_json_dict(complete["map_view"])
    assert replay_map_view_is_renderable(map_view)
    assert map_view.overlay_cells
