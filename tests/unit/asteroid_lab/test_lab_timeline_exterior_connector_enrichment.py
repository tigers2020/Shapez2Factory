"""Lab timeline exterior connector enrichment tests."""

from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
    METRICS_KEY,
    enrich_lab_timeline_frames_with_exterior_connector_plan,
)


def _frame() -> dict:
    return {
        "frame_index": 0,
        "metrics": {},
        "map_view": {
            "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
            "overlay_cells": [],
            "cell_delta": [],
            "annotations": [],
            "bbox": {"min_x": 0, "min_y": -6, "max_x": 5, "max_y": 0},
        },
    }


def test_l2_frame_attaches_metrics_and_overlay() -> None:
    plan_wire = {
        "version": "exterior_connector_plan.v1",
        "planned_connectors": [
            {
                "connector_id": "ext_conn_00",
                "void_coord": {"x": 5, "y": -6},
                "edge": "north",
                "layout_t": "SpaceBelt_Forward",
                "rotation": 1,
                "coords": [{"x": 5, "y": -6}],
            }
        ],
    }
    frames = [_frame()]
    out, frozen = enrich_lab_timeline_frames_with_exterior_connector_plan(
        frames,
        plan_wire=plan_wire,
        l2_complete_frame_index=0,
    )
    # index 0 only — append-stack default is not frame 0 when index omitted
    assert METRICS_KEY in out[0]["metrics"]
    overlay = out[0]["map_view"]["overlay_cells"]
    assert any(c.get("overlay_role") == "planned_exterior_connector" for c in overlay)
    assert any(c.get("tile_type") == "SpaceBelt_Forward" for c in overlay)
    assert frozen is not None


def test_strips_generic_overlay_on_planned_connector_coord() -> None:
    plan_wire = {
        "version": "exterior_connector_plan.v1",
        "planned_connectors": [
            {
                "connector_id": "ext_conn_00",
                "void_coord": {"x": 5, "y": -6},
                "edge": "north",
                "layout_t": "SpaceBelt_Forward",
                "rotation": 1,
                "coords": [{"x": 5, "y": -6}],
            }
        ],
    }
    frame = _frame()
    frame["map_view"]["overlay_cells"] = [
        {"x": 5, "y": -6, "tile_type": "SpaceBelt_Forward", "rotation": 1},
    ]
    out, _frozen = enrich_lab_timeline_frames_with_exterior_connector_plan(
        [frame],
        plan_wire=plan_wire,
        l2_complete_frame_index=0,
    )
    overlay = out[0]["map_view"]["overlay_cells"]
    at = [c for c in overlay if c.get("x") == 5 and c.get("y") == -6]
    assert len(at) == 1
    assert at[0].get("overlay_role") == "planned_exterior_connector"


def test_no_plan_wire_noop() -> None:
    frames = [_frame()]
    out, frozen = enrich_lab_timeline_frames_with_exterior_connector_plan(frames, plan_wire=None)
    assert out == frames
    assert frozen is None


def test_overlay_includes_connector_role_spare() -> None:
    plan_wire = {
        "version": "exterior_connector_plan.v2",
        "planned_connectors": [
            {
                "connector_id": "ext_conn_09",
                "void_coord": {"x": 3, "y": -6},
                "edge": "north",
                "layout_t": "SpaceBelt_Forward",
                "rotation": 1,
                "role": "spare",
                "coords": [{"x": 3, "y": -6}],
            }
        ],
    }
    out, _frozen = enrich_lab_timeline_frames_with_exterior_connector_plan(
        [_frame()],
        plan_wire=plan_wire,
        l2_complete_frame_index=0,
    )
    overlay = out[0]["map_view"]["overlay_cells"]
    at = [c for c in overlay if c.get("x") == 3 and c.get("y") == -6]
    assert len(at) == 1
    assert at[0].get("connector_role") == "spare"
    assert at[0].get("overlay_role") == "planned_exterior_connector"


def test_overlay_unknown_role_normalizes_to_required() -> None:
    plan_wire = {
        "version": "exterior_connector_plan.v2",
        "planned_connectors": [
            {
                "connector_id": "ext_conn_00",
                "void_coord": {"x": 5, "y": -6},
                "role": "future",
                "layout_t": "SpaceBelt_Forward",
                "rotation": 1,
                "coords": [{"x": 5, "y": -6}],
            }
        ],
    }
    out, _frozen = enrich_lab_timeline_frames_with_exterior_connector_plan(
        [_frame()],
        plan_wire=plan_wire,
        l2_complete_frame_index=0,
    )
    overlay = out[0]["map_view"]["overlay_cells"]
    assert overlay[0].get("connector_role") == "required"
