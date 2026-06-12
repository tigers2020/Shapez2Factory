"""Canvas paint-plan adapter parity tests (LabPaintLayers → sprites/overlays)."""

from django_apps.asteroid_lab.replay.replay_cell_index import cell_key
from tests.support.lab_replay_paint_fixtures import frame_38_candidate_miner_fixture
from tests.support.lab_replay_paint_plan import (
    CANDIDATE_RING_STROKE,
    build_effective_cell_view_index,
    canvas_plan_from_paint_layers,
    lab_paint_layers_from_view,
)
from tests.support.lab_replay_sprite_wire import CELL_KIND_STATIC_RELPATH


def _rgba_fill_overlays(plan: dict) -> list[dict]:
    return [
        overlay
        for overlay in plan["overlays"]
        if overlay.get("fill") is not None
        and str(overlay["fill"]).strip().lower().startswith("rgba(")
    ]


def test_frame_38_canvas_plan_has_miner_sprite_no_rgba_fill() -> None:
    frame = frame_38_candidate_miner_fixture()
    index = build_effective_cell_view_index(frame)
    wire = index[cell_key(10, 7, 0)]
    layers = lab_paint_layers_from_view(wire)
    plan = canvas_plan_from_paint_layers(layers, grid_idx=0)

    sprite_rels = {sprite["rel"] for sprite in plan["sprites"]}
    assert "Miner/Layout_ShapeMiner.svg" in sprite_rels
    assert CELL_KIND_STATIC_RELPATH["asteroid_shape_field"] in sprite_rels
    assert _rgba_fill_overlays(plan) == []

    ring = next(o for o in plan["overlays"] if o["kind"] == "candidate_ring")
    assert ring["stroke"] == CANDIDATE_RING_STROKE
    assert ring["fill"] is None


def test_canvas_plan_anti_fade_no_fill_overlay_when_sprite() -> None:
    layers = {
        "terrain": {
            "mode": "field_sprite",
            "rel": CELL_KIND_STATIC_RELPATH["asteroid_shape_field"],
        },
        "occupant": {"rel": "Miner/Layout_ShapeMiner.svg", "rotation": 0},
        "transport": None,
        "chrome": [{"kind": "candidate_ring", "stroke_only": True}],
    }
    plan = canvas_plan_from_paint_layers(layers, grid_idx=5)

    assert plan["sprites"]
    assert any(sprite["idx"] == 5 for sprite in plan["sprites"])
    assert _rgba_fill_overlays(plan) == []
    for overlay in plan["overlays"]:
        assert overlay.get("fill") is None
