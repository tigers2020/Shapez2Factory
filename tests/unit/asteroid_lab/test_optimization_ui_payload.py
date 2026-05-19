"""Optimization replay UI payload guard tests (PR7)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.optimization.replay_frame import OptimizationReplayFrame
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    build_optimization_replay_track_payload,
    deserialize_optimization_replay_frames_from_json,
    optimization_replay_frames_to_json_list,
    validate_optimization_replay_frame_list_payload,
)


def _frame(idx: int, event: OptimizationReplayEventType) -> OptimizationReplayFrame:
    return OptimizationReplayFrame(
        frame_index=idx,
        event_type=event,
        title=event.value,
        description="",
        metrics={},
    )


def test_validate_rejects_non_contiguous_frame_index() -> None:
    raw = [
        {
            "frame_index": 0,
            "event_type": OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED.value,
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        },
        {
            "frame_index": 2,
            "event_type": OptimizationReplayEventType.VALIDATION_COMPLETED.value,
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        },
    ]
    assert validate_optimization_replay_frame_list_payload(raw) == "frame_index_not_contiguous"


def test_validate_rejects_truncation_without_reason() -> None:
    raw = [
        {
            "frame_index": 0,
            "event_type": OptimizationReplayEventType.ROUTE_MATERIALIZED.value,
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {"replay_truncated": True},
        },
    ]
    assert validate_optimization_replay_frame_list_payload(raw) == "truncation_pair_invalid"


def test_round_trip_frames_and_track_truncation_pair() -> None:
    frames = (
        _frame(0, OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED),
        OptimizationReplayFrame(
            frame_index=1,
            event_type=OptimizationReplayEventType.VALIDATION_COMPLETED,
            title="done",
            description="",
            metrics={
                "replay_truncated": True,
                "truncation_reason": "max_replay_frames",
            },
        ),
    )
    raw = optimization_replay_frames_to_json_list(frames)
    assert validate_optimization_replay_frame_list_payload(raw) is None
    back = deserialize_optimization_replay_frames_from_json(raw)
    assert back is not None
    assert len(back) == 2

    track = build_optimization_replay_track_payload(back)
    assert track["metrics"]["replay_truncated"] is True
    assert track["metrics"]["truncation_reason"] == "max_replay_frames"
