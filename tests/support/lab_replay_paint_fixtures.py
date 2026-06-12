"""Shared replay frame fixtures for paint-plan tests."""

from __future__ import annotations


def frame_38_candidate_miner_fixture() -> dict[str, object]:
    """User-reported frame 38 cell (10,7): field + legacy candidate overlay."""
    return {
        "frame_index": 38,
        "event_type": "fixture.frame_38_candidate_miner",
        "map_view": {
            "full_cells": [
                {
                    "x": 10,
                    "y": 7,
                    "kind": "asteroid_shape_field",
                    "transport": "none",
                    "layer": 0,
                    "rotation": 0,
                },
            ],
            "overlay_cells": [
                {
                    "x": 10,
                    "y": 7,
                    "kind": "candidate_miner",
                    "transport": "shape_belt",
                    "rotation": 0,
                    "layer": 0,
                },
            ],
            "cell_delta": [],
        },
    }
