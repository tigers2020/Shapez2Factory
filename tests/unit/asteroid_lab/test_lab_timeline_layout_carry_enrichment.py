"""Layout overlay carry enrichment for sparse tail replay frames."""

from django_apps.asteroid_lab.services.lab_timeline_layout_carry_enrichment import (
    enrich_lab_timeline_frames_with_carried_layout_overlays,
    overlay_cells_are_layout_sparse,
)


def _frame(*, overlay: list[dict[str, object]]) -> dict[str, object]:
    return {
        "frame_index": 0,
        "map_view": {
            "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
            "overlay_cells": overlay,
            "cell_delta": [],
            "annotations": [],
            "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
        },
    }


def test_sparse_tail_inherits_last_rich_overlay_stack() -> None:
    rich = [
        {
            "x": 1,
            "y": 0,
            "overlay_role": "committed_rim_equipment",
            "tile_type": "shape_miner",
        },
        {
            "x": 5,
            "y": -6,
            "overlay_role": "planned_exterior_connector",
            "tile_type": "SpaceBelt_Forward",
        },
    ]
    tail = _frame(overlay=[])
    frames = [_frame(overlay=list(rich)), tail]
    out = enrich_lab_timeline_frames_with_carried_layout_overlays(frames)
    assert out[1]["map_view"]["overlay_cells"] == rich


def test_connector_only_tail_is_still_sparse() -> None:
    assert overlay_cells_are_layout_sparse(
        [{"x": 5, "y": -6, "overlay_role": "planned_exterior_connector"}],
    )


def test_rich_overlay_is_not_sparse() -> None:
    assert not overlay_cells_are_layout_sparse(
        [{"x": 1, "y": 0, "overlay_role": "committed_rim_equipment"}],
    )
