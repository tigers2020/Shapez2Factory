"""Legacy 3B-R append helpers (superseded by lab_rttp_snapshot_compose for product path)."""

from __future__ import annotations

from django_apps.asteroid_lab.services.lab_unified_replay_append import (
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
