"""Replay wire height layer (L=0/1/2) contract tests."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.map_height_layer import (
    enrich_replay_wire_row_with_layer,
    resolve_replay_height_layer,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.runtime_frame_finalize import transient_overlay_cells_to_wire
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayBBox,
    ReplayCell,
    ReplayMapView,
    ReplayOverlayCell,
    ReplayTimelineFrame,
)
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_timeline_frame_json_round_trip,
    replay_timeline_frame_to_json_dict,
)


def test_resolve_shape_miner_is_l0() -> None:
    assert resolve_replay_height_layer(cell_kind="shape_miner", transport_kind="shape_belt") == 0


def test_resolve_fluid_miner_is_l1() -> None:
    assert resolve_replay_height_layer(cell_kind="fluid_miner", transport_kind="fluid_pipe") == 1


def test_resolve_space_belt_is_l2() -> None:
    assert resolve_replay_height_layer(cell_kind="space_belt", transport_kind="shape_belt") == 2


def test_resolve_space_pipe_is_l1() -> None:
    assert resolve_replay_height_layer(cell_kind="space_pipe", transport_kind="fluid_pipe") == 1


def test_resolve_route_probe_path_shape_is_l2() -> None:
    assert (
        resolve_replay_height_layer(
            cell_kind="route_probe_path",
            transport_kind="shape_belt",
        )
        == 2
    )


def test_explicit_layer_passthrough() -> None:
    assert (
        resolve_replay_height_layer(
            cell_kind="shape_miner",
            transport_kind="shape_belt",
            layer=2,
        )
        == 2
    )


def test_transient_overlay_wire_emits_layer() -> None:
    wire = transient_overlay_cells_to_wire(
        (
            ReplayOverlayCell(x=1, y=2, kind="shape_miner", transport="shape_belt"),
            ReplayOverlayCell(x=3, y=4, kind="space_belt", transport="shape_belt"),
        )
    )
    assert wire[0]["layer"] == 0
    assert wire[1]["layer"] == 2


def test_full_cell_wire_emits_layer_from_decode_row() -> None:
    row = enrich_replay_wire_row_with_layer(
        {
            "x": 5,
            "y": 6,
            "cell_kind": "fluid_miner",
            "transport_kind": "fluid_pipe",
            "layer": 1,
        }
    )
    assert row["layer"] == 1


def test_replay_timeline_frame_json_round_trip_preserves_layer_wire() -> None:
    frame = ReplayTimelineFrame(
        frame_index=42,
        phase=ReplayPhase.ROUTE_PROBE,
        event_type=ReplayEventType.ROUTE_PROBE_SUCCEEDED,
        title="Route probe succeeded",
        description="Candidate reached margin.",
        map_view=ReplayMapView(
            base_ref="reconstruction_complete",
            full_cells=(
                ReplayCell(
                    x=1,
                    y=1,
                    kind="shape_miner",
                    transport="shape_belt",
                    layer=0,
                ),
            ),
            overlay_cells=(
                ReplayOverlayCell(
                    x=12,
                    y=5,
                    kind="route_probe_path",
                    transport="shape_belt",
                    layer=2,
                ),
            ),
            bbox=ReplayBBox(min_x=10, min_y=4, max_x=22, max_y=7),
        ),
    )
    before = replay_timeline_frame_to_json_dict(frame)
    restored = replay_timeline_frame_json_round_trip(frame)
    after = replay_timeline_frame_to_json_dict(restored)
    assert before["map_view"]["full_cells"][0]["layer"] == 0
    assert before["map_view"]["overlay_cells"][0]["layer"] == 2
    assert after == before
    assert restored.map_view.full_cells[0].layer == 0
    assert restored.map_view.overlay_cells[0].layer == 2
