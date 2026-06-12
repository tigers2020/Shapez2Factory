"""Step 6.4: layout/bbox coordinate baseline — fixed before spatial helper split."""

from __future__ import annotations

from tests.support.lab_replay_paint_fixtures import frame_38_candidate_miner_fixture
from tests.support.lab_replay_spatial_layout import (
    collect_replay_spatial_coords_for_layout,
    compute_replay_grid_layout_from_frames,
    harvest_spatial_coord_keys,
    layout_spatial_coord_keys,
)
from tests.support.lab_replay_sprite_wire import collect_frame_spatial_targets


def _layout_snapshot(frames: list[dict[str, object]]) -> dict[str, int]:
    return compute_replay_grid_layout_from_frames(frames)


# Baselines captured from legacy ``collectFrameSpatialTargets`` before Step 6.4 split.
HARVEST_LAYOUT_BASELINES: dict[str, dict[str, int]] = {
    "full_map_only": _layout_snapshot(
        [
            {
                "full_map": [
                    {"x": -3, "y": 2, "kind": "asteroid_shape_field", "layer": 0},
                    {"x": 4, "y": -1, "kind": "asteroid_shape_field", "layer": 0},
                ],
            },
        ],
    ),
    "diff_changed_sparse": _layout_snapshot(
        [
            {
                "diff": {
                    "changed": [
                        {"after": {"x": 8, "y": -4, "kind": "space_belt", "layer": 0}},
                    ],
                },
            },
        ],
    ),
    "overlay_json_only": _layout_snapshot(
        [
            {
                "cell_overlay_json": {
                    "cells": [
                        {"x": -2, "y": 5, "kind": "space_pipe", "layer": 0},
                    ],
                },
            },
        ],
    ),
    "frame_38_fixture": _layout_snapshot([frame_38_candidate_miner_fixture()]),
}


def test_layout_helper_is_harvest_coord_superset() -> None:
    fixtures: list[dict[str, object]] = [
        {"full_map": [{"x": 1, "y": 1, "layer": 0}]},
        {
            "map_view": {
                "full_cells": [{"x": 0, "y": 0, "layer": 0}],
                "overlay_cells": [{"x": 2, "y": 0, "layer": 0}],
                "cell_delta": [{"x": 0, "y": 1, "layer": 0}],
            },
        },
        {
            "map_view": {"overlay_cells": [{"x": 3, "y": 3, "layer": 0}]},
            "cell_overlay_json": {"cells": [{"x": 4, "y": 4, "kind": "space_belt", "layer": 0}]},
        },
        frame_38_candidate_miner_fixture(),
    ]
    for frame in fixtures:
        harvest = harvest_spatial_coord_keys(frame)
        layout = layout_spatial_coord_keys(frame)
        assert harvest <= layout, f"missing coords: {harvest - layout}"


def test_layout_grid_matches_harvest_baseline_fixtures() -> None:
    fixture_frames: dict[str, list[dict[str, object]]] = {
        "full_map_only": [
            {
                "full_map": [
                    {"x": -3, "y": 2, "kind": "asteroid_shape_field", "layer": 0},
                    {"x": 4, "y": -1, "kind": "asteroid_shape_field", "layer": 0},
                ],
            },
        ],
        "diff_changed_sparse": [
            {
                "diff": {
                    "changed": [
                        {"after": {"x": 8, "y": -4, "kind": "space_belt", "layer": 0}},
                    ],
                },
            },
        ],
        "overlay_json_only": [
            {
                "cell_overlay_json": {
                    "cells": [
                        {"x": -2, "y": 5, "kind": "space_pipe", "layer": 0},
                    ],
                },
            },
        ],
        "frame_38_fixture": [frame_38_candidate_miner_fixture()],
    }
    for name, frames in fixture_frames.items():
        baseline = HARVEST_LAYOUT_BASELINES[name]
        layout = _layout_snapshot(frames)
        assert layout == baseline, name


def test_new_layout_helper_preserves_harvest_grid_dimensions() -> None:
    """After split, layout helper must not shrink bbox vs harvest baseline."""
    for name, baseline in HARVEST_LAYOUT_BASELINES.items():
        frames_map: dict[str, list[dict[str, object]]] = {
            "full_map_only": [
                {
                    "full_map": [
                        {"x": -3, "y": 2, "kind": "asteroid_shape_field", "layer": 0},
                        {"x": 4, "y": -1, "kind": "asteroid_shape_field", "layer": 0},
                    ],
                },
            ],
            "diff_changed_sparse": [
                {
                    "diff": {
                        "changed": [
                            {"after": {"x": 8, "y": -4, "kind": "space_belt", "layer": 0}},
                        ],
                    },
                },
            ],
            "overlay_json_only": [
                {
                    "cell_overlay_json": {
                        "cells": [
                            {"x": -2, "y": 5, "kind": "space_pipe", "layer": 0},
                        ],
                    },
                },
            ],
            "frame_38_fixture": [frame_38_candidate_miner_fixture()],
        }
        frames = frames_map[name]
        harvest_layout = compute_replay_grid_layout_from_frames(
            frames,
            collect_coords=lambda f: collect_frame_spatial_targets(f),  # type: ignore[arg-type]
        )
        new_layout = compute_replay_grid_layout_from_frames(frames)
        assert new_layout == harvest_layout == baseline, name


def test_layout_helper_includes_required_sources() -> None:
    full_map_frame: dict[str, object] = {
        "full_map": [{"x": 9, "y": 9, "layer": 0}],
    }
    assert (9, 9) in layout_spatial_coord_keys(full_map_frame)

    map_view_frame: dict[str, object] = {
        "map_view": {
            "full_cells": [{"x": 1, "y": 1, "layer": 0}],
            "overlay_cells": [{"x": 2, "y": 2, "layer": 0}],
            "cell_delta": [{"x": 3, "y": 3, "layer": 0}],
        },
        "diff": {
            "changed": [{"after": {"x": 4, "y": 4, "kind": "space_belt", "layer": 0}}],
        },
        "cell_overlay_json": {
            "cells": [{"x": 5, "y": 5, "kind": "space_pipe", "layer": 0}],
        },
    }
    keys = layout_spatial_coord_keys(map_view_frame)
    for x, y in ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5)):
        assert (x, y) in keys
