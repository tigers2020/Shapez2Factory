# tests/unit/asteroid_lab/test_lab_unified_replay_append.py
from __future__ import annotations

from django_apps.asteroid_lab.replay.replay_render_modes import RENDER_MODE_INHERITED_SNAPSHOT
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)
from django_apps.asteroid_lab.services.lab_unified_replay_append import (
    append_algorithm_frames_to_unified_lab_replay,
    last_renderable_map_frame_index,
)


def _map_frame(idx: int) -> dict:
    return {
        "frame_index": idx,
        "event_type": "reconstruction.completed",
        "phase": "reconstruction",
        "title": "Map",
        "map_view": {
            "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
            "cell_delta": [],
            "overlay_cells": [],
            "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
        },
        "inspector": {},
        "metrics": {},
    }


def test_last_renderable_map_frame_index_picks_last_with_cells() -> None:
    frames = [_map_frame(0), {"frame_index": 1, "event_type": "decode.started", "map_view": {}}]
    assert last_renderable_map_frame_index(frames) == 0


def test_append_renumbers_and_adds_inherited_snapshot_tail() -> None:
    map_frames = [_map_frame(0), _map_frame(1)]
    milestones = [
        {
            "frame_index": 0,
            "phase": "rttp_pipeline",
            "event_type": "routing.probe_started",
            "title": "RTTP pipeline started",
            "description": "",
            "inspector": {},
            "metrics": {"k": 1},
        },
        {
            "frame_index": 1,
            "phase": "candidate_generation",
            "event_type": "candidate.generated",
            "title": "Candidates",
            "description": "",
            "inspector": {},
            "metrics": {},
        },
    ]
    out = append_algorithm_frames_to_unified_lab_replay(map_frames, milestones)
    assert len(out) == 4
    assert [f["frame_index"] for f in out] == [0, 1, 2, 3]
    tail = out[2:]
    assert {f["event_type"] for f in tail} <= RTTP_MILESTONE_EVENT_TYPES
    for fr in tail:
        assert fr["render_mode"] == RENDER_MODE_INHERITED_SNAPSHOT
        assert fr["base_frame_index"] == 1
        assert fr["inspector"]["kind"] == "optimization_milestone"
        assert "full_map" not in fr
        assert not fr.get("map_view", {}).get("full_cells")
