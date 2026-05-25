"""Lab timeline terrain_rim_highlight enrichment (output-only)."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.evidence import ASTEROID_FIELD_KINDS
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.services.lab_timeline_rim_enrichment import (
    METRICS_KEY,
    enrich_lab_timeline_frames_with_terrain_rim,
)


def _frame(
    *,
    lab_phase: str,
    event_type: str,
    full_cells: list[dict],
    frame_index: int = 0,
    lab_event_type: str = "reconstruction.begin",
) -> dict:
    return {
        "frame_index": frame_index,
        "phase": "reconstruction",
        "event_type": event_type,
        "title": "t",
        "description": "",
        "inspector": {"lab_phase": lab_phase, "lab_event_type": lab_event_type},
        "metrics": {},
        "map_view": {
            "full_cells": full_cells,
            "cell_delta": [],
            "overlay_cells": [],
            "annotations": [],
            "bbox": {"min_x": 0, "min_y": 0, "max_x": 1, "max_y": 1},
        },
    }


def test_reconstruction_phase_attaches_highlight() -> None:
    field_kind = next(iter(ASTEROID_FIELD_KINDS))
    cells = [{"x": 0, "y": 0, "kind": field_kind}]
    frames = [
        _frame(
            lab_phase="reconstruction",
            event_type="reconstruction.started",
            full_cells=cells,
        )
    ]
    out, frozen = enrich_lab_timeline_frames_with_terrain_rim(frames)
    assert METRICS_KEY in out[0]["metrics"]
    assert frozen is None


def test_post_complete_sets_frozen_and_omits_later_per_frame() -> None:
    field_kind = next(iter(ASTEROID_FIELD_KINDS))
    growing = [
        {"x": 0, "y": 0, "kind": field_kind},
        {"x": 1, "y": 0, "kind": field_kind},
    ]
    frames = [
        _frame(
            lab_phase="reconstruction",
            event_type="reconstruction.started",
            full_cells=[growing[0]],
            frame_index=0,
        ),
        _frame(
            lab_phase="reconstruction",
            event_type=ReplayEventType.RECONSTRUCTION_COMPLETED.value,
            full_cells=growing,
            frame_index=1,
        ),
        _frame(
            lab_phase="reconstruction",
            event_type="optimization.input_loaded",
            full_cells=growing,
            frame_index=2,
        ),
    ]
    out, frozen = enrich_lab_timeline_frames_with_terrain_rim(frames)
    complete_wire = out[1]["metrics"][METRICS_KEY]
    assert frozen == complete_wire
    assert METRICS_KEY not in out[2]["metrics"]


def test_reconstruction_rim_changes_while_field_grows() -> None:
    field_kind = next(iter(ASTEROID_FIELD_KINDS))
    single = [{"x": 0, "y": 0, "kind": field_kind}]
    pair = [
        {"x": 0, "y": 0, "kind": field_kind},
        {"x": 1, "y": 0, "kind": field_kind},
    ]
    frames = [
        _frame(lab_phase="reconstruction", event_type="reconstruction.started", full_cells=single),
        _frame(lab_phase="reconstruction", event_type="reconstruction.started", full_cells=pair),
    ]
    out, _frozen = enrich_lab_timeline_frames_with_terrain_rim(frames)
    assert out[0]["metrics"][METRICS_KEY] != out[1]["metrics"][METRICS_KEY]


def test_decode_frame_omits_highlight() -> None:
    frames = [_frame(lab_phase="decode", event_type="decode.started", full_cells=[])]
    out, frozen = enrich_lab_timeline_frames_with_terrain_rim(frames)
    assert METRICS_KEY not in out[0]["metrics"]
    assert frozen is None
