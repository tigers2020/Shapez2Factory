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


def test_compose_reindexes_global_frame_index_monotonic() -> None:
    lab = (_frame(10, phase=ReplayPhase.DECODE, event=ReplayEventType.DECODE_STARTED, tag="lab"),)
    opt = (
        _frame(
            5,
            phase=ReplayPhase.OPTIMIZATION_INPUT,
            event=ReplayEventType.OPTIMIZATION_INPUT_LOADED,
            tag="opt",
        ),
    )
    out = compose_unified_timeline(lab_frames=lab, optimization_frames=opt)
    assert [f.frame_index for f in out] == [0, 1]
    assert out[0].inspector["source_frame_index"] == 10
    assert out[1].inspector["source_frame_index"] == 5


def test_compose_lab_precedes_optimization() -> None:
    lab = (_frame(0, phase=ReplayPhase.DECODE, event=ReplayEventType.DECODE_STARTED, tag="lab"),)
    opt = (
        _frame(
            0,
            phase=ReplayPhase.VALIDATION,
            event=ReplayEventType.VALIDATION_COMPLETED,
            tag="opt",
        ),
    )
    out = compose_unified_timeline(lab_frames=lab, optimization_frames=opt)
    assert out[0].phase == ReplayPhase.DECODE
    assert out[1].phase == ReplayPhase.VALIDATION


def test_compose_truncation_sets_metrics_pair() -> None:
    lab = tuple(
        _frame(
            i,
            phase=ReplayPhase.RECONSTRUCTION,
            event=ReplayEventType.RECONSTRUCTION_STARTED,
            tag=f"l{i}",
        )
        for i in range(3)
    )
    opt = tuple(
        _frame(
            i,
            phase=ReplayPhase.OPTIMIZATION_INPUT,
            event=ReplayEventType.OPTIMIZATION_INPUT_LOADED,
            tag=f"o{i}",
        )
        for i in range(3)
    )
    out = compose_unified_timeline(lab_frames=lab, optimization_frames=opt, max_frames=4)
    assert len(out) == 4
    last = out[-1]
    assert last.metrics.get("replay_truncated") is True
    assert last.metrics.get("truncation_reason") == "max_unified_replay_frames"


def test_compose_empty_inputs() -> None:
    assert compose_unified_timeline(lab_frames=(), optimization_frames=()) == ()
