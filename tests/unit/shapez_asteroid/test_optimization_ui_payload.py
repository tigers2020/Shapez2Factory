"""Sequence 9 — optimization replay track envelope (debug/export; not merged into Lab page)."""

from __future__ import annotations

import json

from django_apps.shapez_asteroid.optimization.dto import OptimizationReplayFrame
from django_apps.shapez_asteroid.optimization.enums import OptimizationReplayEventType
from django_apps.shapez_asteroid.optimization.optimization_replay import (
    OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY,
    TRACK_ID,
    OptimizationReplayRecorder,
    build_optimization_replay_track_payload,
    empty_optimization_replay_track_payload,
)


def test_optimization_replay_track_payload_empty() -> None:
    empty = empty_optimization_replay_track_payload()
    built = build_optimization_replay_track_payload(())
    assert empty == built
    assert empty["track_id"] == TRACK_ID
    assert empty["frame_count"] == 0
    assert empty["frames"] == []
    assert empty["metrics"]["event_type_counts"] == {}


def test_optimization_replay_track_payload_serializes_frames() -> None:
    frames = (
        OptimizationReplayFrame(
            frame_index=0,
            event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
            title="a",
            description="d0",
            visible_cells=(),
            overlay_cells=(),
            metrics={"k": 1},
        ),
        OptimizationReplayFrame(
            frame_index=1,
            event_type=OptimizationReplayEventType.GENOME_EVALUATED,
            title="b",
            description="d1",
            visible_cells=(),
            overlay_cells=(),
            metrics={},
        ),
    )
    payload = build_optimization_replay_track_payload(frames)
    assert payload["frame_count"] == 2
    out_frames = payload["frames"]
    assert len(out_frames) == 2
    assert out_frames[0]["frame_index"] == 0
    assert out_frames[0]["event_type"] == OptimizationReplayEventType.CANDIDATE_GENERATED.value
    assert out_frames[0]["title"] == "a"
    assert out_frames[0]["metrics"] == {"k": 1}
    assert out_frames[1]["event_type"] == OptimizationReplayEventType.GENOME_EVALUATED.value


def test_optimization_replay_track_payload_event_type_counts() -> None:
    frames = (
        OptimizationReplayFrame(
            0,
            OptimizationReplayEventType.CANDIDATE_REJECTED,
            "x",
            "",
            (),
            (),
            {},
        ),
        OptimizationReplayFrame(
            1,
            OptimizationReplayEventType.CANDIDATE_REJECTED,
            "y",
            "",
            (),
            (),
            {},
        ),
        OptimizationReplayFrame(
            2,
            OptimizationReplayEventType.BEST_GENOME_SELECTED,
            "z",
            "",
            (),
            (),
            {},
        ),
    )
    counts = build_optimization_replay_track_payload(frames)["metrics"]["event_type_counts"]
    assert counts == {
        OptimizationReplayEventType.BEST_GENOME_SELECTED.value: 1,
        OptimizationReplayEventType.CANDIDATE_REJECTED.value: 2,
    }
    assert list(counts.keys()) == sorted(counts.keys())


def test_optimization_replay_track_payload_truncated_aggregate() -> None:
    frames = (
        OptimizationReplayFrame(
            0,
            OptimizationReplayEventType.CANDIDATE_GENERATED,
            "t",
            "",
            (),
            (),
            {"replay_truncated": True},
        ),
        OptimizationReplayFrame(
            1,
            OptimizationReplayEventType.CANDIDATE_GENERATED,
            "u",
            "",
            (),
            (),
            {},
        ),
    )
    m = build_optimization_replay_track_payload(frames)["metrics"]
    assert m["replay_truncated"] is True


def test_optimization_replay_track_payload_json_safe() -> None:
    payload = build_optimization_replay_track_payload(())
    json.dumps(payload)
    rec = OptimizationReplayRecorder(max_frames=3)
    for i in range(5):
        rec.record_replay_frame(
            event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
            title=str(i),
            description="",
            metrics={"i": i},
        )
    json.dumps(build_optimization_replay_track_payload(rec.frames))


def test_optimization_track_uses_enum_values() -> None:
    f = OptimizationReplayFrame(
        0,
        OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
        "t",
        "d",
        (),
        (),
        {},
    )
    et = build_optimization_replay_track_payload((f,))["frames"][0]["event_type"]
    assert et == OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED.value
    assert et == "optimization.input_loaded"
    assert "OPTIMIZATION_INPUT_LOADED" not in str(et)


def test_optimization_track_payload_deterministic() -> None:
    frames = (
        OptimizationReplayFrame(
            0,
            OptimizationReplayEventType.GENOME_GENERATED,
            "g",
            "",
            (),
            (),
            {"seed": 7},
        ),
        OptimizationReplayFrame(
            1,
            OptimizationReplayEventType.GENOME_GENERATED,
            "g2",
            "",
            (),
            (),
            {"seed": 8},
        ),
    )
    a = json.dumps(build_optimization_replay_track_payload(frames), sort_keys=True)
    b = json.dumps(build_optimization_replay_track_payload(frames), sort_keys=True)
    assert a == b


def test_lab_style_replay_payload_without_parallel_track_key_is_json_safe() -> None:
    """Lab UI bundle shape stays valid without merging a second replay track."""
    base = {
        "lab_replay_frames_json": [{"id": 10, "phase": "p", "event_type": "lab.custom"}],
        "lab_initial_replay_frame_json": {"id": 10},
        "has_replay_frames": True,
        "lab_ui_initial": {"frame": 0, "totalFrames": 1},
    }
    json.dumps(base)
    assert OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY not in base
