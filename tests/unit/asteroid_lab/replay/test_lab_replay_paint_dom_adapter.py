"""DOM paint-plan adapter parity tests (LabPaintLayers → tone/sprite DOM plan)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.effective_cell_view import merge_effective_cell_view
from django_apps.asteroid_lab.replay.effective_cell_wire import effective_cell_to_wire
from django_apps.asteroid_lab.replay.replay_wire_read_sanitize import (
    sanitize_replay_wire_cell_for_read,
)
from tests.support.lab_replay_paint_fixtures import frame_38_candidate_miner_fixture
from tests.support.lab_replay_paint_plan import (
    build_dom_plan_for_wire,
    dom_plan_from_paint_layers,
    lab_paint_layers_from_view,
)


def _merged_view_from_frame(frame: dict, x: int, y: int):
    mv = frame["map_view"]
    full = next(c for c in mv["full_cells"] if c["x"] == x and c["y"] == y)
    ov = next(c for c in mv["overlay_cells"] if c["x"] == x and c["y"] == y)
    view = merge_effective_cell_view(
        x=x,
        y=y,
        frame_index=int(frame.get("frame_index", 0)),
        full_cell=sanitize_replay_wire_cell_for_read(full),
        delta_cell=None,
        overlay_cells=[sanitize_replay_wire_cell_for_read(ov)],
    )
    assert view is not None
    return dict(effective_cell_to_wire(view))


def test_frame_38_dom_plan_ring_not_full_fill() -> None:
    wire = _merged_view_from_frame(frame_38_candidate_miner_fixture(), 10, 7)
    layers = lab_paint_layers_from_view(wire)
    plan = dom_plan_from_paint_layers(layers, overlay_kind="candidate_miner")
    tokens = set(plan["tone_classes"].split())
    assert plan["sprite_rel"] == "Miner/Layout_ShapeMiner.svg"
    assert plan["skip_full_fill"] is True
    assert "lab-overlay-candidate-miner-ring" in tokens
    assert "lab-overlay-candidate-miner" not in tokens


def test_dom_plan_anti_fade_no_full_fill_class_when_sprite() -> None:
    layers = {
        "terrain": {"mode": "field_sprite", "rel": "AsteroidField/AsteroidField_Shape.svg"},
        "occupant": {"rel": "Miner/Layout_ShapeMiner.svg", "rotation": 0},
        "transport": None,
        "chrome": [{"kind": "candidate_ring", "stroke_only": True}],
    }
    plan = dom_plan_from_paint_layers(layers, overlay_kind="candidate_miner")
    tokens = set(plan["tone_classes"].split())
    assert plan["skip_full_fill"] is True
    assert "lab-overlay-candidate-miner" not in tokens
    assert "lab-overlay-candidate-miner-ring" in tokens


def test_dom_plan_transport_does_not_set_sprite_rel() -> None:
    """Slice 4: skipFullFill may use transport for tone; spriteRel is occupant-only."""
    layers = {
        "terrain": None,
        "occupant": None,
        "transport": {"rel": "SpaceBelt/SpaceBelt_Forward.svg", "rotation": 0},
        "chrome": [],
    }
    plan = dom_plan_from_paint_layers(layers)
    assert plan["sprite_rel"] is None
    assert plan["skip_full_fill"] is True


def test_dom_plan_void_candidate_allows_full_fill_fallback() -> None:
    layers = {
        "terrain": None,
        "occupant": None,
        "transport": None,
        "chrome": [{"kind": "candidate_ring", "stroke_only": True}],
    }
    plan = dom_plan_from_paint_layers(layers, overlay_kind="candidate_miner")
    tokens = set(plan["tone_classes"].split())
    assert plan["sprite_rel"] is None
    assert plan["skip_full_fill"] is False
    assert "lab-overlay-candidate-miner" in tokens


def test_inner_field_block_dom_plan_from_merged_wire_without_sources() -> None:
    wire = {
        "frame_index": 38,
        "coord": {"x": 5, "y": 8, "layer": 0},
        "terrain": {"kind": "asteroid_shape_field", "tile_type": None},
        "occupant": {"kind": "none", "rotation": None},
        "transport": {"kind": "none", "tile_id": None, "simulation": None},
        "output": {"transport_kind": "space_belt"},
        "overlay_role": "inner_field_block",
        "sources": {},
    }
    plan = build_dom_plan_for_wire(wire)
    assert plan["sprite"] is None
    assert plan["sprite_rel"] is None
    assert plan["data_attrs"]["overlay_role"] == "inner_field_block"
    assert plan["data_attrs"]["output_transport_kind"] == "space_belt"
    assert plan["data_attrs"]["transport_kind"] == "none"
    assert "ring-violet-400" in plan["root_classes"]
    assert plan["candidate_observation"] is False


def test_candidate_dom_plan_preserves_ring_without_fabricated_sprite() -> None:
    wire = _merged_view_from_frame(frame_38_candidate_miner_fixture(), 10, 7)
    plan = build_dom_plan_for_wire(wire)
    assert plan["sprite_rel"] == "Miner/Layout_ShapeMiner.svg"
    assert "lab-overlay-candidate-miner-ring" in plan["root_classes"]
    assert plan["fallback_token"] is None
