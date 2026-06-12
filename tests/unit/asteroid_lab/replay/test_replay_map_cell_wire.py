"""Ingress/egress contract tests for replay map cell wire."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.replay.replay_map_cell_wire import (
    ReplayMapCellWireError,
    replay_cell_delta_from_wire,
    replay_cell_delta_to_wire,
    replay_cell_from_wire,
    replay_cell_to_wire,
    replay_overlay_cell_from_wire,
    wire_field_kind,
    wire_field_tile_type,
    wire_field_transport,
)
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayBBox,
    ReplayCell,
    ReplayCellDelta,
    ReplayMapView,
)
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_map_view_to_json_dict,
    replay_timeline_frame_json_round_trip,
    replay_timeline_frame_to_json_dict,
)


def test_wire_field_accessors_accept_legacy_aliases() -> None:
    row = {
        "cell_kind": "shape_miner",
        "transport_kind": "shape_belt",
        "sprite_identifier": "ShapeMiner",
    }
    assert wire_field_kind(row) == "shape_miner"
    assert wire_field_transport(row) == "shape_belt"
    assert wire_field_tile_type(row) == "ShapeMiner"


def test_replay_cell_from_wire_reads_legacy_aliases() -> None:
    cell = replay_cell_from_wire(
        {
            "x": 1,
            "y": 2,
            "cell_kind": "fluid_miner",
            "transport_kind": "fluid_pipe",
            "sprite_identifier": "FluidMiner",
            "rotation": "90",
        },
        field_prefix="cell",
    )
    assert cell == ReplayCell(
        x=1,
        y=2,
        kind="fluid_miner",
        transport="fluid_pipe",
        tile_type="FluidMiner",
        rotation=90,
    )


def test_replay_cell_delta_from_wire_defaults_op() -> None:
    delta = replay_cell_delta_from_wire(
        {"x": 0, "y": 0, "kind": "space_belt", "transport": "shape_belt"},
        field_prefix="cell_delta",
    )
    assert delta.op == "set"


def test_replay_overlay_cell_from_wire_rejects_non_int_x() -> None:
    with pytest.raises(ReplayMapCellWireError, match="overlay.x"):
        replay_overlay_cell_from_wire({"x": "bad", "y": 0})


def test_cell_wire_round_trip_preserves_snapshot_fields() -> None:
    cell = ReplayCell(
        x=5,
        y=6,
        kind="shape_miner",
        transport="shape_belt",
        tile_type="ShapeMiner",
        rotation=45,
        layer=0,
    )
    restored = replay_cell_from_wire(replay_cell_to_wire(cell), field_prefix="cell")
    assert restored == cell


def test_replay_cell_to_wire_emits_legacy_sprite_alias_and_layer() -> None:
    cell = ReplayCell(
        x=3,
        y=4,
        kind="shape_miner",
        transport="shape_belt",
        tile_type="ShapeMiner",
        rotation=90,
    )
    wire = replay_cell_to_wire(cell)
    assert wire["x"] == 3
    assert wire["y"] == 4
    assert wire["kind"] == "shape_miner"
    assert wire["transport"] == "shape_belt"
    assert wire["tile_type"] == "ShapeMiner"
    assert wire["sprite_identifier"] == "ShapeMiner"
    assert wire["rotation"] == 90
    assert wire["layer"] == 0


def test_replay_cell_delta_to_wire_includes_op() -> None:
    delta = ReplayCellDelta(
        x=1,
        y=2,
        kind="space_belt",
        transport="shape_belt",
        op="clear",
        tile_type="SpaceBelt_I",
        rotation=180,
        layer=2,
    )
    wire = replay_cell_delta_to_wire(delta)
    assert wire["op"] == "clear"
    assert wire["layer"] == 2
    assert wire["sprite_identifier"] == "SpaceBelt_I"


def test_replay_map_view_egress_uses_cell_wire_module() -> None:
    map_view = ReplayMapView(
        bbox=ReplayBBox(min_x=0, min_y=0, max_x=5, max_y=5),
        full_cells=(
            ReplayCell(
                x=0,
                y=0,
                kind="fluid_miner",
                transport="fluid_pipe",
                tile_type="FluidMiner",
            ),
        ),
        cell_delta=(
            ReplayCellDelta(
                x=1,
                y=1,
                kind="space_pipe",
                transport="fluid_pipe",
                tile_type="SpacePipe_I",
            ),
        ),
    )
    payload = replay_map_view_to_json_dict(map_view)
    full = payload["full_cells"]
    assert isinstance(full, list)
    assert full[0] == replay_cell_to_wire(map_view.full_cells[0])
    delta = payload["cell_delta"]
    assert isinstance(delta, list)
    assert delta[0] == replay_cell_delta_to_wire(map_view.cell_delta[0])


def test_timeline_frame_round_trip_unchanged_after_wire_module() -> None:
    from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
    from django_apps.asteroid_lab.replay.timeline_dtos import ReplayTimelineFrame

    frame = ReplayTimelineFrame(
        frame_index=7,
        phase=ReplayPhase.DECODE,
        event_type=ReplayEventType.DECODE_STARTED,
        title="t",
        description="d",
        map_view=ReplayMapView(
            bbox=ReplayBBox(min_x=0, min_y=0, max_x=3, max_y=3),
            full_cells=(ReplayCell(x=1, y=1, kind="asteroid_shape_field"),),
            cell_delta=(
                ReplayCellDelta(x=2, y=2, kind="space_belt", transport="shape_belt"),
            ),
        ),
    )
    before = replay_timeline_frame_to_json_dict(frame)
    restored = replay_timeline_frame_json_round_trip(frame)
    after = replay_timeline_frame_to_json_dict(restored)
    assert after == before
