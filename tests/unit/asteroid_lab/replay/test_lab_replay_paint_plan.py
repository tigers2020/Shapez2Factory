"""LabPaintLayers resolver parity tests (Python authority for JS reviewers).

Python ↔ JS field mapping (Slice 2):
| Python (TypedDict) | JS (LabReplayPaintPlan) |
|--------------------|-------------------------|
| stroke_only        | strokeOnly              |
| transport_kind     | transportKind           |
"""

from django_apps.asteroid_lab.replay.effective_cell_view import merge_effective_cell_view
from django_apps.asteroid_lab.replay.effective_cell_wire import effective_cell_to_wire
from django_apps.asteroid_lab.replay.replay_cell_index import cell_key
from django_apps.asteroid_lab.replay.replay_wire_read_sanitize import (
    sanitize_replay_wire_cell_for_read,
)
from tests.support.lab_replay_paint_fixtures import frame_38_candidate_miner_fixture
from tests.support.lab_replay_paint_plan import (
    BACKGROUND_FILL,
    VOID_FILL,
    build_effective_cell_view_index,
    lab_paint_layers_from_view,
)
from tests.support.lab_replay_sprite_wire import CELL_KIND_STATIC_RELPATH


def test_frame_38_fixture_has_map_view_at_10_7() -> None:
    frame = frame_38_candidate_miner_fixture()
    mv = frame["map_view"]
    full = {(c["x"], c["y"]): c for c in mv["full_cells"]}
    ov = {(c["x"], c["y"]): c for c in mv["overlay_cells"]}
    assert (10, 7) in full
    assert full[(10, 7)]["kind"] == "asteroid_shape_field"
    assert (10, 7) in ov
    assert ov[(10, 7)]["kind"] == "candidate_miner"


def _merged_view_from_frame(frame: dict, x: int, y: int):
    mv = frame["map_view"]
    full = next(c for c in mv["full_cells"] if c["x"] == x and c["y"] == y)
    overlays = [c for c in mv["overlay_cells"] if c["x"] == x and c["y"] == y]
    full = sanitize_replay_wire_cell_for_read(full)
    overlays = [sanitize_replay_wire_cell_for_read(c) for c in overlays]
    view = merge_effective_cell_view(
        x=x,
        y=y,
        frame_index=frame.get("frame_index"),
        full_cell=full,
        overlay_cells=overlays,
    )
    assert view is not None
    return effective_cell_to_wire(view)


def test_frame_38_candidate_miner_paint_layers() -> None:
    wire = _merged_view_from_frame(frame_38_candidate_miner_fixture(), 10, 7)
    layers = lab_paint_layers_from_view(wire)
    assert layers["occupant"] is not None
    assert layers["occupant"]["rel"] == "Miner/Layout_ShapeMiner.svg"
    assert layers["transport"] is None
    assert any(c["kind"] == "candidate_ring" for c in layers["chrome"])
    assert layers["terrain"] is not None
    assert layers["terrain"]["mode"] == "field_sprite"
    assert layers["terrain"]["rel"] == CELL_KIND_STATIC_RELPATH["asteroid_shape_field"]


def test_python_paint_layers_frame_38_contract_snapshot() -> None:
    """Stable contract snapshot for JS parity reviewers."""
    wire = _merged_view_from_frame(frame_38_candidate_miner_fixture(), 10, 7)
    layers = lab_paint_layers_from_view(wire)
    assert layers == {
        "terrain": {
            "mode": "field_sprite",
            "rel": CELL_KIND_STATIC_RELPATH["asteroid_shape_field"],
        },
        "occupant": {"rel": "Miner/Layout_ShapeMiner.svg", "rotation": 0},
        "transport": None,
        "chrome": [{"kind": "candidate_ring", "stroke_only": True}],
    }


def test_transport_sprite_does_not_override_candidate_miner() -> None:
    wire = {
        "frame_index": 38,
        "coord": {"x": 10, "y": 7, "layer": 0},
        "terrain": {"kind": "asteroid_shape_field", "tile_type": None},
        "occupant": {"kind": "candidate_miner", "rotation": 0},
        "transport": {"kind": "space_belt", "tile_id": "SpaceBelt_Forward", "simulation": None},
        "output": {"transport_kind": "space_belt"},
        "sources": {},
    }
    layers = lab_paint_layers_from_view(wire)
    assert layers["occupant"]["rel"] == "Miner/Layout_ShapeMiner.svg"
    assert layers["transport"] is None


def test_build_effective_cell_view_index_frame_38() -> None:
    frame = frame_38_candidate_miner_fixture()
    index = build_effective_cell_view_index(frame)
    key = cell_key(10, 7, 0)
    assert key in index
    assert index[key]["occupant"]["kind"] == "candidate_miner"
    assert index[key]["output"]["transport_kind"] == "space_belt"


def test_anti_fade_precondition_no_background_fill_when_occupant_sprite() -> None:
    wire = _merged_view_from_frame(frame_38_candidate_miner_fixture(), 10, 7)
    layers = lab_paint_layers_from_view(wire)
    assert layers["occupant"] is not None
    terrain = layers.get("terrain")
    if terrain is not None:
        assert terrain["mode"] != "background_fill"


def test_background_fill_allowed_only_when_no_sprite() -> None:
    empty_wire = {
        "frame_index": 0,
        "coord": {"x": 1, "y": 1, "layer": 0},
        "terrain": {"kind": "empty", "tile_type": None},
        "occupant": {"kind": "none", "rotation": None},
        "transport": {"kind": "none", "tile_id": None, "simulation": None},
        "output": {"transport_kind": "none"},
        "sources": {},
    }
    empty_layers = lab_paint_layers_from_view(empty_wire)
    assert empty_layers["occupant"] is None
    assert empty_layers["transport"] is None
    assert empty_layers["terrain"] is not None
    assert empty_layers["terrain"]["mode"] == "background_fill"
    assert empty_layers["terrain"]["fill"] == BACKGROUND_FILL

    void_wire = {
        **empty_wire,
        "terrain": {"kind": "internal_void", "tile_type": None},
    }
    void_layers = lab_paint_layers_from_view(void_wire)
    assert void_layers["occupant"] is None
    assert void_layers["transport"] is None
    assert void_layers["terrain"] is not None
    assert void_layers["terrain"]["mode"] == "void_fill"
    assert void_layers["terrain"]["fill"] == VOID_FILL

    field_wire = {
        **empty_wire,
        "terrain": {"kind": "asteroid_shape_field", "tile_type": None},
    }
    field_layers = lab_paint_layers_from_view(field_wire)
    assert field_layers["occupant"] is None
    assert field_layers["transport"] is None
    assert field_layers["terrain"] is not None
    assert field_layers["terrain"]["mode"] == "field_sprite"
    assert field_layers["terrain"]["rel"] == CELL_KIND_STATIC_RELPATH["asteroid_shape_field"]

    for layers in (empty_layers, void_layers, field_layers):
        terrain = layers.get("terrain")
        if terrain is not None and layers["occupant"] is None and layers["transport"] is None:
            assert terrain["mode"] != "background_fill" or terrain.get("fill") == BACKGROUND_FILL


def test_build_effective_cell_view_index_unions_cell_overlay_json() -> None:
    from tests.support.lab_replay_sprite_wire import overlay_fallback_fixture_frame

    frame = overlay_fallback_fixture_frame()
    index = build_effective_cell_view_index(frame)
    pipe_key = cell_key(2, 0, 2)
    assert pipe_key in index
    view = index[pipe_key]
    assert view["transport"]["kind"] == "space_pipe"
    assert view["transport"]["tile_id"] == "SpacePipe_Forward"
