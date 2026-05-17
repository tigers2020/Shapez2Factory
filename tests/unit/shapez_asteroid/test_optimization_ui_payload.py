"""Sequence 9 — optimization replay track Lab payload adapter."""

from __future__ import annotations

import json

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import OptimizationReplayFrame
from django_apps.shapez_asteroid.optimization.enums import OptimizationReplayEventType
from django_apps.shapez_asteroid.optimization.optimization_replay import (
    OptimizationReplayRecorder,
    optimization_replay_frames_to_json_list,
)
from django_apps.shapez_asteroid.optimization.optimization_ui_payload import (
    OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY,
    OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY,
    TRACK_ID,
    build_optimization_replay_track_payload,
    classify_persisted_optimization_replay_frames_value,
    deserialize_optimization_replay_frames_from_json,
    diagnostic_reason_after_failed_optimization_replay_scan,
    empty_optimization_replay_track_payload,
    empty_optimization_replay_track_payload_with_diagnostic,
    merge_optimization_track_into_lab_payload,
    validate_optimization_replay_frame_list_payload,
)


def test_deserialize_optimization_replay_round_trips_recorder_output() -> None:
    rec = OptimizationReplayRecorder()
    rec.record_replay_frame(
        event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
        title="g",
        description="d",
        visible_cells=(Coord(1, 2),),
        overlay_cells=(),
        metrics={"k": 1},
    )
    raw = optimization_replay_frames_to_json_list(rec.frames)
    got = deserialize_optimization_replay_frames_from_json(raw)
    assert got == rec.frames


def test_recorder_truncation_round_trip_passes_frame_list_guard() -> None:
    rec = OptimizationReplayRecorder(max_frames=2)
    for i in range(4):
        rec.record_replay_frame(
            event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
            title=str(i),
            description="",
            visible_cells=(),
            overlay_cells=(),
            metrics={},
        )
    raw = optimization_replay_frames_to_json_list(rec.frames)
    assert validate_optimization_replay_frame_list_payload(raw) is True
    assert deserialize_optimization_replay_frames_from_json(raw) == rec.frames


def test_deserialize_rejects_truncation_without_reason() -> None:
    raw = [
        {
            "frame_index": 0,
            "event_type": OptimizationReplayEventType.CANDIDATE_GENERATED.value,
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {"replay_truncated": True},
        }
    ]
    assert deserialize_optimization_replay_frames_from_json(raw) is None
    assert validate_optimization_replay_frame_list_payload(raw) is False


def test_deserialize_rejects_unknown_event_type() -> None:
    raw = [
        {
            "frame_index": 0,
            "event_type": "not.a.real.event",
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        }
    ]
    assert deserialize_optimization_replay_frames_from_json(raw) is None


def test_deserialize_rejects_non_sequential_frame_index() -> None:
    raw = [
        {
            "frame_index": 1,
            "event_type": OptimizationReplayEventType.GENOME_GENERATED.value,
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        }
    ]
    assert deserialize_optimization_replay_frames_from_json(raw) is None


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
            {"replay_truncated": True, "truncation_reason": "first_reason"},
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
    assert m["truncation_reason"] == "first_reason"


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


def test_merge_optimization_track_preserves_existing_payload_fields() -> None:
    base = {
        "lab_replay_frames_json": [{"id": 1, "frame_index": 0}],
        "lab_initial_replay_frame_json": {"id": 1},
        "has_replay_frames": True,
        "extra": {"nested": [1, 2]},
    }
    merged = merge_optimization_track_into_lab_payload(base, ())
    assert merged["lab_replay_frames_json"] == base["lab_replay_frames_json"]
    assert merged["has_replay_frames"] is True
    assert merged["extra"] == base["extra"]
    assert OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY in merged


def test_merge_optimization_track_does_not_mutate_base_payload() -> None:
    base: dict[str, object] = {"a": 1, "nested": {"x": 2}}
    merged = merge_optimization_track_into_lab_payload(base, ())
    assert OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY not in base
    assert OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY in merged
    assert merged is not base


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


def test_persisted_optimization_replay_rejects_non_list_payload() -> None:
    assert validate_optimization_replay_frame_list_payload({"x": 1}) is False
    assert validate_optimization_replay_frame_list_payload("[]") is False
    assert validate_optimization_replay_frame_list_payload(None) is False


def test_validate_optimization_replay_frame_list_payload_accepts_empty_list() -> None:
    assert validate_optimization_replay_frame_list_payload([]) is True


def test_persisted_optimization_replay_requires_continuous_frame_index() -> None:
    raw = [
        {
            "frame_index": 0,
            "event_type": OptimizationReplayEventType.CANDIDATE_GENERATED.value,
            "title": "a",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        },
        {
            "frame_index": 2,
            "event_type": OptimizationReplayEventType.CANDIDATE_GENERATED.value,
            "title": "b",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        },
    ]
    assert validate_optimization_replay_frame_list_payload(raw) is False


def test_persisted_optimization_replay_rejects_unknown_event_type_guard() -> None:
    raw = [
        {
            "frame_index": 0,
            "event_type": "bogus.event",
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        }
    ]
    assert validate_optimization_replay_frame_list_payload(raw) is False


def test_persisted_optimization_replay_truncation_contract() -> None:
    bad = [
        {
            "frame_index": 0,
            "event_type": OptimizationReplayEventType.CANDIDATE_GENERATED.value,
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {"replay_truncated": True},
        }
    ]
    assert validate_optimization_replay_frame_list_payload(bad) is False
    good = [
        {
            "frame_index": 0,
            "event_type": OptimizationReplayEventType.CANDIDATE_GENERATED.value,
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {"replay_truncated": True, "truncation_reason": "cells"},
        }
    ]
    assert validate_optimization_replay_frame_list_payload(good) is True
    frames = deserialize_optimization_replay_frames_from_json(good)
    assert frames is not None
    track = build_optimization_replay_track_payload(frames)
    assert track["metrics"]["replay_truncated"] is True
    assert track["metrics"]["truncation_reason"] == "cells"


def test_build_optimization_replay_track_payload_aggregates_first_truncation_reason() -> None:
    frames = (
        OptimizationReplayFrame(
            0,
            OptimizationReplayEventType.CANDIDATE_GENERATED,
            "a",
            "",
            (),
            (),
            {"replay_truncated": True, "truncation_reason": "alpha"},
        ),
        OptimizationReplayFrame(
            1,
            OptimizationReplayEventType.CANDIDATE_GENERATED,
            "b",
            "",
            (),
            (),
            {"replay_truncated": True, "truncation_reason": "beta"},
        ),
    )
    m = build_optimization_replay_track_payload(frames)["metrics"]
    assert m["truncation_reason"] == "alpha"


def test_build_optimization_replay_track_payload_omits_truncation_reason_when_not_truncated() -> (
    None
):
    frames = (
        OptimizationReplayFrame(
            0,
            OptimizationReplayEventType.CANDIDATE_GENERATED,
            "a",
            "",
            (),
            (),
            {"truncation_reason": "ignored_when_not_truncated"},
        ),
    )
    m = build_optimization_replay_track_payload(frames)["metrics"]
    assert m["replay_truncated"] is False
    assert "truncation_reason" not in m


def test_build_truncated_without_frame_reason_uses_unknown() -> None:
    """In-memory frames may omit the pair; track still exposes a non-empty reason (§6.1)."""

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
    )
    m = build_optimization_replay_track_payload(frames)["metrics"]
    assert m["replay_truncated"] is True
    assert m["truncation_reason"] == "unknown"


def test_existing_replay_payload_without_optimization_still_valid() -> None:
    base = {
        "lab_replay_frames_json": [{"id": 10, "phase": "p", "event_type": "lab.custom"}],
        "lab_initial_replay_frame_json": {"id": 10},
        "has_replay_frames": True,
        "lab_ui_initial": {"frame": 0, "totalFrames": 1},
    }
    json.dumps(base)
    merged = merge_optimization_track_into_lab_payload(base, ())
    json.dumps(merged)
    for k in base:
        assert merged[k] == base[k]
    assert merged[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]["frame_count"] == 0


def test_missing_optimization_replay_sets_diagnostic_reason() -> None:
    assert diagnostic_reason_after_failed_optimization_replay_scan([{}]) == (
        "missing_optimization_replay"
    )
    assert diagnostic_reason_after_failed_optimization_replay_scan(()) == (
        "missing_optimization_replay"
    )


def test_empty_optimization_replay_sets_diagnostic_reason() -> None:
    assert classify_persisted_optimization_replay_frames_value([]) == (
        "empty_optimization_replay_frames"
    )


def test_invalid_optimization_replay_payload_sets_diagnostic_reason() -> None:
    assert classify_persisted_optimization_replay_frames_value({"x": 1}) == (
        "invalid_optimization_replay_payload"
    )
    assert classify_persisted_optimization_replay_frames_value(None) == (
        "invalid_optimization_replay_payload"
    )


def test_invalid_truncation_contract_sets_diagnostic_reason() -> None:
    raw = [
        {
            "frame_index": 0,
            "event_type": OptimizationReplayEventType.CANDIDATE_GENERATED.value,
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {"replay_truncated": True},
        }
    ]
    assert classify_persisted_optimization_replay_frames_value(raw) == (
        "invalid_truncation_contract"
    )


def test_unknown_event_type_sets_diagnostic_reason() -> None:
    raw = [
        {
            "frame_index": 0,
            "event_type": "not.a.real.event",
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        }
    ]
    assert classify_persisted_optimization_replay_frames_value(raw) == (
        "unsupported_or_unknown_event_type"
    )


def test_valid_optimization_replay_has_no_diagnostic_reason() -> None:
    frames = (
        OptimizationReplayFrame(
            0,
            OptimizationReplayEventType.CANDIDATE_GENERATED,
            "a",
            "d0",
            (),
            (),
            {"k": 1},
        ),
    )
    payload = build_optimization_replay_track_payload(frames)
    assert OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY not in payload["metrics"]


def test_diagnostic_reason_does_not_change_replay_metrics() -> None:
    empty = empty_optimization_replay_track_payload()
    diag = empty_optimization_replay_track_payload_with_diagnostic(
        "empty_optimization_replay_frames"
    )
    em = dict(empty["metrics"])  # type: ignore[arg-type]
    dm = dict(diag["metrics"])  # type: ignore[arg-type]
    del dm[OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY]
    assert em == dm
