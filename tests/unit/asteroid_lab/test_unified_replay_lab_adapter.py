"""Phase 9B — Lab ReplayFrame → UnifiedReplayFrame adapter tests."""

from __future__ import annotations

from dataclasses import asdict

import pytest

from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_DECODE_RAW_LOADED,
    EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED,
    EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT,
)
from django_apps.asteroid_lab.replay.lab_unified_adapter import (
    LAB_EVENT_TYPE_TO_UNIFIED,
    LabUnifiedAdapterError,
    lab_replay_row_to_unified,
    lab_snapshot_event_payload_copy,
    lab_snapshot_event_to_unified,
)
from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.unified_event_coverage import SUPPORTED_BY_9B_LAB_ADAPTER
from django_apps.asteroid_lab.replay.unified_serialization import unified_replay_frame_json_round_trip
from django_apps.asteroid_lab.services.dto import ReplayFrameRowDTO, SnapshotEventDTO


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
    frame = lab_snapshot_event_to_unified(event, frame_index=7)
    assert frame.frame_index == 7
    assert frame.phase == ReplayPhase.DECODE
    assert frame.event_type == ReplayEventType.DECODE_STARTED
    assert len(frame.map_view.full_cells) == 1
    assert frame.map_view.full_cells[0].kind == "asteroid"
    assert frame.map_view.bbox.min_x == 1
    assert frame.map_view.bbox.max_x == 1
    assert frame.inspector["lab_event_type"] == EVENT_TYPE_DECODE_RAW_LOADED
    assert frame.metrics["entry_count"] == 3


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
    frame = lab_snapshot_event_to_unified(event, frame_index=12)
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
    frame = lab_snapshot_event_to_unified(event, frame_index=3)
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
    frame = lab_replay_row_to_unified(row)
    assert frame.frame_index == 42
    assert frame.metrics.get("from_row") is True
    assert frame.metrics.get("entry_count") == 3


def test_lab_adapter_does_not_mutate_source_frame() -> None:
    event = _decode_event()
    before = lab_snapshot_event_payload_copy(event)
    lab_snapshot_event_to_unified(event, frame_index=0)
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
    lab_replay_row_to_unified(row)
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
    with pytest.raises(LabUnifiedAdapterError):
        lab_snapshot_event_to_unified(event, frame_index=0)


def test_lab_adapter_uses_replay_bbox_wire_shape() -> None:
    event = SnapshotEventDTO(
        event_key="bbox",
        phase="decode",
        event_type=EVENT_TYPE_DECODE_RAW_LOADED,
        title="t",
        full_map=[_cell_row(x=2, y=4), _cell_row(x=10, y=1)],
    )
    frame = lab_snapshot_event_to_unified(event, frame_index=0)
    bbox = frame.map_view.bbox
    assert bbox.min_x == 2
    assert bbox.min_y == 1
    assert bbox.max_x == 10
    assert bbox.max_y == 4


def test_lab_adapter_event_type_mapping_is_enum_only() -> None:
    frame = lab_snapshot_event_to_unified(_decode_event(), frame_index=0)
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
    frame = lab_snapshot_event_to_unified(event, frame_index=0)
    assert frame.metrics["custom"] == 1
    assert frame.metrics["replay_truncated"] is False


def test_lab_adapter_deterministic_json_round_trip() -> None:
    frame = lab_snapshot_event_to_unified(_decode_event(), frame_index=99)
    restored = unified_replay_frame_json_round_trip(frame)
    assert restored == frame


def test_lab_adapter_event_mapping_matrix_is_explicit() -> None:
    assert set(LAB_EVENT_TYPE_TO_UNIFIED.keys()) == {
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
    for unified in LAB_EVENT_TYPE_TO_UNIFIED.values():
        assert unified in SUPPORTED_BY_9B_LAB_ADAPTER


def test_lab_adapter_rejects_candidate_event_type() -> None:
    event = SnapshotEventDTO(
        event_key="cand",
        phase="decode",
        event_type="candidate.generated",
        title="t",
        full_map=[_cell_row(x=0, y=0)],
    )
    with pytest.raises(LabUnifiedAdapterError):
        lab_snapshot_event_to_unified(event, frame_index=0)
