"""Optimization replay UI payload guard tests (PR7)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.optimization.replay_frame import OptimizationReplayFrame
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    build_optimization_replay_track_payload,
    deserialize_optimization_replay_frames_from_json,
    deserialize_optimization_replay_frames_lenient,
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


def test_invalid_event_type_skips_frame_not_whole_track() -> None:
    """A single invalid event_type must not drop the entire track (lenient read path)."""
    valid_event = OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED.value
    raw = [
        {
            "frame_index": 0,
            "event_type": valid_event,
            "title": "first",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        },
        {
            "frame_index": 1,
            "event_type": "capacity.plan_created_UNKNOWN_SUFFIX",  # invalid
            "title": "bad",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        },
        {
            "frame_index": 2,
            "event_type": OptimizationReplayEventType.VALIDATION_COMPLETED.value,
            "title": "last",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        },
    ]
    # strict validator rejects the whole payload
    assert validate_optimization_replay_frame_list_payload(raw) == "invalid_event_type"
    assert deserialize_optimization_replay_frames_from_json(raw) is None

    # lenient deserialize skips the bad frame, keeps the valid ones
    frames, omitted = deserialize_optimization_replay_frames_lenient(raw)
    assert omitted == 1
    assert len(frames) == 2
    assert frames[0].event_type == OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED
    assert frames[1].event_type == OptimizationReplayEventType.VALIDATION_COMPLETED
    # frame indices are re-assigned contiguously
    assert frames[0].frame_index == 0
    assert frames[1].frame_index == 1


def test_lenient_deserialize_all_invalid_returns_empty() -> None:
    raw = [
        {
            "frame_index": 0,
            "event_type": "not_a_valid_event",
            "title": "",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        },
    ]
    frames, omitted = deserialize_optimization_replay_frames_lenient(raw)
    assert frames == ()
    assert omitted == 1


def test_lenient_deserialize_non_list_returns_empty() -> None:
    frames, omitted = deserialize_optimization_replay_frames_lenient("not a list")
    assert frames == ()
    assert omitted == 0
