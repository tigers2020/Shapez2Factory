"""Layer 02 append-stack timeline helpers."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.services.lab_layer02_timeline import (
    LAYER02_EVENT_TYPE,
    build_layer02_timeline_frame_dict,
    resolve_l2_complete_frame_index,
)
from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
    METRICS_KEY,
    enrich_lab_timeline_frames_with_exterior_connector_plan,
)


def _recon_frame() -> dict:
    return {
        "frame_index": 0,
        "event_type": ReplayEventType.RECONSTRUCTION_COMPLETED.value,
        "phase": "reconstruction",
        "map_view": {
            "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
            "overlay_cells": [],
            "cell_delta": [],
            "annotations": [],
            "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
        },
        "metrics": {},
    }


def test_resolve_l2_complete_frame_index_from_exterior_event() -> None:
    frames = [_recon_frame(), {"frame_index": 1, "event_type": LAYER02_EVENT_TYPE}]
    assert resolve_l2_complete_frame_index(frames) == 1


def test_enrich_skips_frames_before_l2_complete_index() -> None:
    plan_wire = {
        "version": "exterior_connector_plan.v1",
        "planned_connectors": [
            {
                "connector_id": "ext_conn_00",
                "void_coord": {"x": 5, "y": -6},
                "layout_t": "SpaceBelt_Forward",
                "rotation": 1,
            }
        ],
    }
    l2_frame = build_layer02_timeline_frame_dict(
        plan_wire=plan_wire,
        source_frame=_recon_frame(),
        complete_map=None,
    )
    frames = [_recon_frame(), l2_frame]
    out, frozen = enrich_lab_timeline_frames_with_exterior_connector_plan(
        frames,
        plan_wire=plan_wire,
        l2_complete_frame_index=1,
    )
    assert METRICS_KEY not in (out[0].get("metrics") or {})
    assert METRICS_KEY in (out[1].get("metrics") or {})
    assert frozen is not None
    assert len(out[0]["map_view"]["overlay_cells"]) == 0


def test_deprecated_layer02_wrapper_omits_l3() -> None:
    from django_apps.asteroid_lab.services.lab_layer02_timeline import (
        build_layer02_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        golden_5x5_complete_map,
    )
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
    )

    frames = build_layer02_runtime_replay_frames(
        plan_wire=exterior_plan_wire_for_golden(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        complete_map=golden_5x5_complete_map(),
    )
    assert "layer03_rim_bundle_scan_begin" not in [f["event_type"] for f in frames]


def test_enrich_noop_when_l2_index_unresolved() -> None:
    plan_wire = {"version": "exterior_connector_plan.v1", "planned_connectors": []}
    frames = [_recon_frame()]
    out, frozen = enrich_lab_timeline_frames_with_exterior_connector_plan(
        frames,
        plan_wire=plan_wire,
        l2_complete_frame_index=None,
    )
    assert out == frames
    assert frozen is None
