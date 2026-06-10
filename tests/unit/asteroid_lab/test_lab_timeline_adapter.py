"""Phase 9B ??Lab ReplayFrame ??ReplayTimelineFrame adapter tests."""

from __future__ import annotations

from dataclasses import asdict

import pytest

from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_DECODE_RAW_LOADED,
    EVENT_TYPE_RECONSTRUCTION_BEGIN,
    EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED,
    EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT,
)
from django_apps.asteroid_lab.replay.lab_timeline_adapter import (
    LAB_EVENT_TYPE_TO_TIMELINE,
    LabTimelineAdapterError,
    lab_replay_row_to_timeline_frame,
    lab_snapshot_event_payload_copy,
    lab_snapshot_event_to_timeline_frame,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.replay_event_coverage import SUPPORTED_BY_9B_LAB_ADAPTER
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_timeline_frame_json_round_trip,
    replay_timeline_frame_to_json_dict,
)
from django_apps.asteroid_lab.services.dto import ReplayFrameRowDTO, SnapshotEventDTO
from django_apps.asteroid_lab.snapshots.equipment_bundles import build_equipment_bundles


def _cell_row(*, x: int, y: int, kind: str = "asteroid") -> dict[str, object]:
    return {
        "x": x,
        "y": y,
        "layer": 0,
        "cell_kind": kind,
        "transport_kind": "none",
    }


def _decode_event() -> SnapshotEventDTO:
    return SnapshotEventDTO(
        event_key="step0_decode_raw",
        phase="decode",
        phase_step="raw",
        event_type=EVENT_TYPE_DECODE_RAW_LOADED,
        title="Decoded blueprint (raw)",
        description="raw decode",
        full_map=[_cell_row(x=1, y=2)],
        metrics_json={"entry_count": 3},
    )


def test_lab_replay_frame_to_unified_decode_frame() -> None:
    event = _decode_event()
    frame = lab_snapshot_event_to_timeline_frame(event, frame_index=7)
    assert frame.frame_index == 7
    assert frame.phase == ReplayPhase.DECODE
    assert frame.event_type == ReplayEventType.DECODE_STARTED
    assert len(frame.map_view.full_cells) == 1
    assert frame.map_view.full_cells[0].kind == "asteroid"
    assert frame.map_view.bbox.min_x == 1
    assert frame.map_view.bbox.max_x == 1
    assert frame.inspector["lab_event_type"] == EVENT_TYPE_DECODE_RAW_LOADED
    assert frame.metrics["entry_count"] == 3


def test_lab_adapter_promotes_replay_trace_diff_to_overlay_cells() -> None:
    """Reconstruction trace markers in diff.added must appear in map_view.overlay_cells."""

    event = SnapshotEventDTO(
        event_key="step4_00_wall_projection",
        phase="reconstruction",
        phase_step="wall_projection",
        event_type=EVENT_TYPE_RECONSTRUCTION_BEGIN,
        title="Wall Projection",
        description="trace",
        full_map=[_cell_row(x=1, y=1, kind="unknown")],
        diff={
            "added": [
                {
                    "x": 1,
                    "y": 1,
                    "layer": None,
                    "cell_kind": "internal_void",
                    "transport_kind": "none",
                    "tile_type": "",
                    "_replay_trace": True,
                },
                {
                    "x": 2,
                    "y": 1,
                    "layer": None,
                    "cell_kind": "asteroid_shape_field",
                    "transport_kind": "none",
                    "tile_type": "",
                },
            ],
            "removed": [],
            "changed": [],
        },
    )
    frame = lab_snapshot_event_to_timeline_frame(event, frame_index=5)
    assert len(frame.map_view.overlay_cells) == 1
    ov = frame.map_view.overlay_cells[0]
    assert ov.x == 1 and ov.y == 1
    assert ov.kind == "internal_void"
    assert frame.diff is not None
    assert len(frame.diff.get("added") or []) == 2


def test_lab_adapter_trace_overlay_wins_on_same_xy_as_persisted_overlay() -> None:
    event = SnapshotEventDTO(
        event_key="step4_trace",
        phase="reconstruction",
        phase_step="flood_seed",
        event_type=EVENT_TYPE_RECONSTRUCTION_BEGIN,
        title="Flood Seed",
        full_map=[_cell_row(x=0, y=0, kind="unknown")],
        cell_overlay_json={"cells": [_cell_row(x=0, y=0, kind="unknown")]},
        diff={
            "added": [
                {
                    "x": 0,
                    "y": 0,
                    "cell_kind": "internal_void",
                    "transport_kind": "none",
                    "_replay_trace": True,
                }
            ],
            "removed": [],
            "changed": [],
        },
    )
    frame = lab_snapshot_event_to_timeline_frame(event, frame_index=0)
    assert len(frame.map_view.overlay_cells) == 1
    assert frame.map_view.overlay_cells[0].kind == "internal_void"


def test_lab_adapter_preserves_diff_on_wire_json() -> None:
    event = SnapshotEventDTO(
        event_key="step4_barrier",
        phase="reconstruction",
        phase_step="barrier_build",
        event_type=EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED,
        title="Barrier Build",
        full_map=[_cell_row(x=3, y=4, kind="unknown")],
        diff={
            "added": [
                {
                    "x": 3,
                    "y": 4,
                    "cell_kind": "internal_void",
                    "_replay_trace": True,
                }
            ],
            "removed": [],
            "changed": [],
        },
    )
    frame = lab_snapshot_event_to_timeline_frame(event, frame_index=0)
    wire = replay_timeline_frame_to_json_dict(frame)
    assert isinstance(wire.get("diff"), dict)
    assert len(wire["diff"].get("added") or []) == 1
    assert wire["map_view"]["overlay_cells"]
    restored = replay_timeline_frame_json_round_trip(frame)
    assert restored.diff == frame.diff
    assert len(restored.map_view.overlay_cells) == len(frame.map_view.overlay_cells)
    restored_overlay = restored.map_view.overlay_cells[0]
    source_overlay = frame.map_view.overlay_cells[0]
    assert restored_overlay.x == source_overlay.x
    assert restored_overlay.y == source_overlay.y
    assert restored_overlay.kind == source_overlay.kind
    assert restored_overlay.layer == 0


def test_lab_replay_frame_to_unified_reconstruction_frame() -> None:
    event = SnapshotEventDTO(
        event_key="step4_shell",
        phase="reconstruction",
        phase_step="shell_row_span",
        event_type=EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED,
        title="Shell detected",
        description="trace",
        full_map=[_cell_row(x=5, y=6, kind="internal_void")],
        metrics_json={"trace_event_type": "shell_row_span"},
    )
    frame = lab_snapshot_event_to_timeline_frame(event, frame_index=12)
    assert frame.phase == ReplayPhase.RECONSTRUCTION
    assert frame.event_type == ReplayEventType.RECONSTRUCTION_STARTED
    assert frame.metrics["trace_event_type"] == "shell_row_span"


def test_lab_adapter_maps_layout_cleanup_to_reconstruction() -> None:
    event = SnapshotEventDTO(
        event_key="step1_cleanup_transport",
        phase="layout_cleanup",
        phase_step="transport",
        event_type=EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT,
        title="After transport cleanup",
        description="baseline",
        full_map=[_cell_row(x=0, y=0)],
    )
    frame = lab_snapshot_event_to_timeline_frame(event, frame_index=3)
    assert frame.phase == ReplayPhase.RECONSTRUCTION
    assert frame.event_type == ReplayEventType.RECONSTRUCTION_STARTED
    assert frame.inspector["lab_phase"] == "layout_cleanup"


def test_lab_adapter_preserves_global_frame_index() -> None:
    event = _decode_event()
    row = ReplayFrameRowDTO(
        id=99,
        frame_index=42,
        frame_key="step0_decode_raw",
        phase="decode",
        title="Decoded blueprint (raw)",
        description="raw decode",
        frame_payload=dict(asdict(event)),
        cell_overlay_json={},
        metric_snapshot_json={"from_row": True},
        is_placeholder=False,
        is_keyframe=True,
    )
    frame = lab_replay_row_to_timeline_frame(row)
    assert frame.frame_index == 42
    assert frame.inspector["replay_frame_id"] == 99
    assert frame.metrics.get("from_row") is True
    assert frame.metrics.get("entry_count") == 3


def test_lab_adapter_preserves_equipment_bundles_on_wire() -> None:
    miner_rows = [
        _cell_row(x=-1, y=0, kind="shape_miner"),
        _cell_row(x=-1, y=1, kind="shape_miner_extension"),
    ]
    bundles = build_equipment_bundles(miner_rows)
    assert bundles
    event = SnapshotEventDTO(
        event_key="step1_cleanup_transport",
        phase="layout_cleanup",
        phase_step="transport",
        event_type=EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT,
        title="After transport cleanup",
        description="baseline",
        full_map=miner_rows,
        cell_overlay_json={"cells": miner_rows, "equipment_bundles": bundles},
    )
    row = ReplayFrameRowDTO(
        id=7,
        frame_index=0,
        frame_key="step1_cleanup_transport",
        phase="layout_cleanup",
        title="After transport cleanup",
        description="baseline",
        frame_payload=dict(asdict(event)),
        cell_overlay_json={"cells": miner_rows, "equipment_bundles": bundles},
        metric_snapshot_json={},
        is_placeholder=False,
        is_keyframe=False,
    )
    frame = lab_replay_row_to_timeline_frame(row)
    wire_bundles = frame.cell_overlay_json.get("equipment_bundles")
    assert isinstance(wire_bundles, list) and len(wire_bundles) == len(bundles)
    payload = replay_timeline_frame_to_json_dict(frame)
    assert "cell_overlay_json" in payload
    assert payload["cell_overlay_json"]["equipment_bundles"]


def test_lab_adapter_does_not_mutate_source_frame() -> None:
    event = _decode_event()
    before = lab_snapshot_event_payload_copy(event)
    lab_snapshot_event_to_timeline_frame(event, frame_index=0)
    after = lab_snapshot_event_payload_copy(event)
    assert before == after

    payload_before = dict(asdict(event))
    row = ReplayFrameRowDTO(
        id=1,
        frame_index=0,
        frame_key=event.event_key,
        phase=event.phase,
        title=event.title,
        description=event.description,
        frame_payload=payload_before,
        cell_overlay_json={},
        metric_snapshot_json={},
        is_placeholder=False,
        is_keyframe=False,
    )
    lab_replay_row_to_timeline_frame(row)
    assert payload_before == dict(asdict(event))


def test_lab_adapter_rejects_unrenderable_map_view() -> None:
    event = SnapshotEventDTO(
        event_key="empty",
        phase="decode",
        event_type=EVENT_TYPE_DECODE_RAW_LOADED,
        title="t",
        full_map=[],
        cell_overlay_json={},
    )
    with pytest.raises(LabTimelineAdapterError):
        lab_snapshot_event_to_timeline_frame(event, frame_index=0)


def test_lab_adapter_uses_replay_bbox_wire_shape() -> None:
    event = SnapshotEventDTO(
        event_key="bbox",
        phase="decode",
        event_type=EVENT_TYPE_DECODE_RAW_LOADED,
        title="t",
        full_map=[_cell_row(x=2, y=4), _cell_row(x=10, y=1)],
    )
    frame = lab_snapshot_event_to_timeline_frame(event, frame_index=0)
    bbox = frame.map_view.bbox
    assert bbox.min_x == 2
    assert bbox.min_y == 1
    assert bbox.max_x == 10
    assert bbox.max_y == 4


def test_lab_adapter_event_type_mapping_is_enum_only() -> None:
    frame = lab_snapshot_event_to_timeline_frame(_decode_event(), frame_index=0)
    assert frame.event_type in ReplayEventType
    assert frame.event_type in SUPPORTED_BY_9B_LAB_ADAPTER


def test_lab_adapter_metrics_are_output_only_passthrough() -> None:
    event = SnapshotEventDTO(
        event_key="m",
        phase="decode",
        event_type=EVENT_TYPE_DECODE_RAW_LOADED,
        title="t",
        full_map=[_cell_row(x=0, y=0)],
        metrics_json={"replay_truncated": False, "custom": 1},
    )
    frame = lab_snapshot_event_to_timeline_frame(event, frame_index=0)
    assert frame.metrics["custom"] == 1
    assert frame.metrics["replay_truncated"] is False


def test_lab_adapter_deterministic_json_round_trip() -> None:
    frame = lab_snapshot_event_to_timeline_frame(_decode_event(), frame_index=99)
    restored = replay_timeline_frame_json_round_trip(frame)
    assert restored == frame


def test_lab_adapter_event_mapping_matrix_is_explicit() -> None:
    assert set(LAB_EVENT_TYPE_TO_TIMELINE.keys()) == {
        "decode.raw_loaded",
        "decode.normalized",
        "reconstruction.begin",
        "reconstruction.clear_old_layout",
        "reconstruction.shell_detected",
        "reconstruction.external_flood_fill",
        "reconstruction.internal_void_detected",
        "reconstruction.interior_patch_marked",
        "reconstruction.mineable_finalized",
        "reconstruction.map_complete",
        "replay.snapshot.cleanup_transport",
        "replay.snapshot.cleanup_extractor",
        "replay.snapshot.cleanup_extension",
        "replay.snapshot.reconstruction",
    }
    for timeline_event in LAB_EVENT_TYPE_TO_TIMELINE.values():
        assert timeline_event in SUPPORTED_BY_9B_LAB_ADAPTER


def test_lab_adapter_rejects_candidate_event_type() -> None:
    event = SnapshotEventDTO(
        event_key="cand",
        phase="decode",
        event_type="candidate.generated",
        title="t",
        full_map=[_cell_row(x=0, y=0)],
    )
    with pytest.raises(LabTimelineAdapterError):
        lab_snapshot_event_to_timeline_frame(event, frame_index=0)


def test_lab_adapter_preserves_transport_tile_type() -> None:
    """full_map row with tile_type must survive the adapter as map_view.full_cells[].tile_type."""
    event = SnapshotEventDTO(
        event_key="step0_with_belt",
        phase="decode",
        event_type=EVENT_TYPE_DECODE_RAW_LOADED,
        title="raw decode",
        full_map=[
            {
                "x": 1,
                "y": 0,
                "cell_kind": "space_belt",
                "transport_kind": "shape_belt",
                "tile_type": "SpaceBelt_Forward",
                "rotation": 0,
            }
        ],
    )
    frame = lab_snapshot_event_to_timeline_frame(event, frame_index=0)
    assert len(frame.map_view.full_cells) == 1
    cell = frame.map_view.full_cells[0]
    assert cell.tile_type == "SpaceBelt_Forward"
    assert cell.rotation == 0


def test_lab_adapter_transport_tile_type_round_trips_as_sprite_identifier() -> None:
    """After JSON round-trip, sprite_identifier alias must equal tile_type."""
    event = SnapshotEventDTO(
        event_key="rt_belt",
        phase="decode",
        event_type=EVENT_TYPE_DECODE_RAW_LOADED,
        title="raw",
        full_map=[
            {
                "x": 2,
                "y": 1,
                "cell_kind": "space_pipe",
                "transport_kind": "fluid_pipe",
                "tile_type": "SpacePipe_LeftTurn",
                "rotation": 1,
            }
        ],
    )
    frame = lab_snapshot_event_to_timeline_frame(event, frame_index=0)
    restored = replay_timeline_frame_json_round_trip(frame)
    cell = restored.map_view.full_cells[0]
    assert cell.tile_type == "SpacePipe_LeftTurn"
    assert cell.rotation == 1


def test_lab_adapter_sprite_identifier_fallback_in_input() -> None:
    """Rows carrying sprite_identifier (no tile_type) must still resolve the sprite key."""
    event = SnapshotEventDTO(
        event_key="alias_only",
        phase="decode",
        event_type=EVENT_TYPE_DECODE_RAW_LOADED,
        title="raw",
        full_map=[
            {
                "x": 3,
                "y": 0,
                "cell_kind": "space_belt",
                "transport_kind": "shape_belt",
                "sprite_identifier": "SpaceBelt_RightTurn",
                "rotation": 3,
            }
        ],
    )
    frame = lab_snapshot_event_to_timeline_frame(event, frame_index=0)
    cell = frame.map_view.full_cells[0]
    assert cell.tile_type == "SpaceBelt_RightTurn"
    assert cell.rotation == 3


def test_lab_adapter_sprite_identifier_in_serialized_json() -> None:
    """Serialized map_view JSON must contain sprite_identifier == tile_type for every cell."""
    from django_apps.asteroid_lab.replay.timeline_serialization import (
        replay_timeline_frame_to_json_dict,
    )

    event = SnapshotEventDTO(
        event_key="serial_check",
        phase="decode",
        event_type=EVENT_TYPE_DECODE_RAW_LOADED,
        title="raw",
        full_map=[
            {
                "x": 1,
                "y": 0,
                "cell_kind": "space_belt",
                "transport_kind": "shape_belt",
                "tile_type": "SpaceBelt_Forward",
                "rotation": 0,
            },
            {
                "x": 2,
                "y": 0,
                "cell_kind": "space_pipe",
                "transport_kind": "fluid_pipe",
                "tile_type": "SpacePipe_LeftTurn",
                "rotation": 1,
            },
        ],
    )
    frame = lab_snapshot_event_to_timeline_frame(event, frame_index=0)
    d = replay_timeline_frame_to_json_dict(frame)
    for cell in d["map_view"]["full_cells"]:
        assert "sprite_identifier" in cell, "sprite_identifier alias missing from serialized cell"
        assert (
            cell["sprite_identifier"] == cell["tile_type"]
        ), "sprite_identifier must equal tile_type in wire JSON"
