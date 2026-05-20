"""Phase 9D — unified timeline composer tests."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.unified_dtos import (
    ReplayBBox,
    ReplayCell,
    ReplayMapView,
    UnifiedReplayFrame,
)
from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.unified_timeline_composer import compose_unified_timeline


def _frame(
    idx: int,
    *,
    phase: ReplayPhase,
    event: ReplayEventType,
    tag: str,
) -> UnifiedReplayFrame:
    cell = ReplayCell(x=idx, y=0, kind=tag, transport="none")
    return UnifiedReplayFrame(
        frame_index=idx,
        phase=phase,
        event_type=event,
        title=tag,
        description="",
        map_view=ReplayMapView(
            bbox=ReplayBBox(min_x=idx, min_y=0, max_x=idx, max_y=0),
            full_cells=(cell,),
        ),
        inspector={"tag": tag},
        metrics={},
    )


def test_compose_preserves_cell_overlay_json() -> None:
    lab_cell = ReplayCell(x=1, y=0, kind="shape_miner", transport="none")
    lab = (
        UnifiedReplayFrame(
            frame_index=0,
            phase=ReplayPhase.DECODE,
            event_type=ReplayEventType.DECODE_STARTED,
            title="lab",
            description="",
            map_view=ReplayMapView(
                bbox=ReplayBBox(min_x=1, min_y=0, max_x=1, max_y=0),
                full_cells=(lab_cell,),
            ),
            inspector={},
            metrics={},
            cell_overlay_json={
                "equipment_bundles": [{"bundle_id": 1, "cells_json": [{"x": 1, "y": 0}]}]
            },
        ),
    )
    out = compose_unified_timeline(lab_frames=lab)
    assert out[0].cell_overlay_json.get("equipment_bundles")


def test_compose_preserves_inspector_replay_frame_id() -> None:
    lab_cell = ReplayCell(x=1, y=0, kind="lab", transport="none")
    lab = (
        UnifiedReplayFrame(
            frame_index=3,
            phase=ReplayPhase.DECODE,
            event_type=ReplayEventType.DECODE_STARTED,
            title="lab",
            description="",
            map_view=ReplayMapView(
                bbox=ReplayBBox(min_x=1, min_y=0, max_x=1, max_y=0),
                full_cells=(lab_cell,),
            ),
            inspector={"replay_frame_id": 42, "tag": "lab"},
            metrics={},
        ),
    )
    out = compose_unified_timeline(lab_frames=lab)
    assert len(out) == 1
    assert out[0].inspector["replay_frame_id"] == 42


def test_compose_reindexes_global_frame_index_monotonic() -> None:
    lab = (
        _frame(10, phase=ReplayPhase.DECODE, event=ReplayEventType.DECODE_STARTED, tag="a"),
        _frame(11, phase=ReplayPhase.DECODE, event=ReplayEventType.DECODE_COMPLETED, tag="b"),
    )
    out = compose_unified_timeline(lab_frames=lab)
    assert [f.frame_index for f in out] == [0, 1]
    assert out[0].inspector["source_frame_index"] == 10
    assert out[1].inspector["source_frame_index"] == 11


def test_compose_truncation_sets_metrics_pair() -> None:
    lab = tuple(
        _frame(
            i,
            phase=ReplayPhase.RECONSTRUCTION,
            event=ReplayEventType.RECONSTRUCTION_STARTED,
            tag=f"l{i}",
        )
        for i in range(6)
    )
    out = compose_unified_timeline(lab_frames=lab, max_frames=4)
    assert len(out) == 4
    last = out[-1]
    assert last.metrics.get("replay_truncated") is True
    assert last.metrics.get("truncation_reason") == "max_unified_replay_frames"


def test_unified_timeline_truncation_records_dropped_frame_count() -> None:
    lab = tuple(
        _frame(
            i,
            phase=ReplayPhase.RECONSTRUCTION,
            event=ReplayEventType.RECONSTRUCTION_STARTED,
            tag=f"l{i}",
        )
        for i in range(6)
    )
    out = compose_unified_timeline(lab_frames=lab, max_frames=4)
    assert len(out) == 4
    last = out[-1]
    assert last.metrics.get("dropped_frame_count") == 2


def test_compose_empty_inputs() -> None:
    assert compose_unified_timeline(lab_frames=()) == ()


def test_replay_head_truncate_retains_result_layout() -> None:
    """When the timeline exceeds max_frames, RESULT_LAYOUT must be retained."""
    lab = tuple(
        _frame(
            i,
            phase=ReplayPhase.RECONSTRUCTION,
            event=ReplayEventType.RECONSTRUCTION_STARTED,
            tag=f"lab{i}",
        )
        for i in range(8)
    ) + (
        _frame(
            99,
            phase=ReplayPhase.RESULT,
            event=ReplayEventType.RESULT_LAYOUT,
            tag="result",
        ),
    )
    out = compose_unified_timeline(lab_frames=lab, max_frames=8)
    event_types = [f.event_type for f in out]
    assert ReplayEventType.RESULT_LAYOUT in event_types
    last = out[-1]
    assert last.metrics.get("replay_truncated") is True


def test_replay_truncation_retains_first_reconstruction_keyframe() -> None:
    """The first RECONSTRUCTION_COMPLETED keyframe must survive truncation."""
    lab = tuple(
        _frame(
            i,
            phase=ReplayPhase.RECONSTRUCTION,
            event=(
                ReplayEventType.RECONSTRUCTION_COMPLETED
                if i == 0
                else ReplayEventType.RECONSTRUCTION_STARTED
            ),
            tag=f"lab{i}",
        )
        for i in range(6)
    )
    out = compose_unified_timeline(lab_frames=lab, max_frames=4)
    event_types = [f.event_type for f in out]
    assert ReplayEventType.RECONSTRUCTION_COMPLETED in event_types
