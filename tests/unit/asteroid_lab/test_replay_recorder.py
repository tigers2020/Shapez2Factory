"""A4 ``ReplayRecorder`` ??append-only frames, policy, ordering."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.dto import ReplayRecordingPolicyDTO, SnapshotEventDTO
from django_apps.asteroid_lab.services.replay_recorder import (
    ReplayRecorder,
    ReplayRecorderCapExceeded,
)


@pytest.fixture
def replay_track() -> m.ReplayTrack:
    p = m.AsteroidProject.objects.create(name="RR", slug="rr-proj")
    return m.ReplayTrack.objects.create(project=p, track_key="rr-track")


def _ev(
    *,
    key: str,
    event_type: str,
    phase: str = "decode",
    title: str = "t",
    overlay: dict | None = None,
    metrics: dict | None = None,
    before: dict | None = None,
    after: dict | None = None,
    delta: dict | None = None,
    decision: bool = True,
) -> SnapshotEventDTO:
    return SnapshotEventDTO(
        event_key=key,
        phase=phase,
        phase_step="s",
        event_type=event_type,
        title=title,
        description="",
        before_state_json=dict(before or {}),
        after_state_json=dict(after or {}),
        delta_json=dict(delta or {}),
        cell_overlay_json=dict(overlay or {"k": 1}),
        focus_cells_json=[],
        is_decision_point=decision,
        metrics_json=dict(metrics or {"fitness": 0.1}),
    )


@pytest.mark.django_db
def test_replay_recorder_one_event_one_frame(replay_track: m.ReplayTrack) -> None:
    r = ReplayRecorder(replay_track.id)
    ev = _ev(key="k0", event_type=et.EVENT_TYPE_DECODE_RAW_LOADED)
    out = r.record_event(ev)
    assert out is not None
    assert out.frame_index == 0
    assert out.replay_track_id == replay_track.id
    row = m.ReplayFrame.objects.get(pk=out.replay_frame_id)
    assert row.frame_key == "k0"
    assert row.cell_overlay_json == {"k": 1}
    assert row.metric_snapshot_json == {"fitness": 0.1}


@pytest.mark.django_db
def test_replay_recorder_preserves_frame_ordering(replay_track: m.ReplayTrack) -> None:
    r = ReplayRecorder(replay_track.id)
    a = r.record_event(_ev(key="a", event_type=et.EVENT_TYPE_DECODE_RAW_LOADED, title="A"))
    b = r.record_event(_ev(key="b", event_type=et.EVENT_TYPE_DECODE_NORMALIZED, title="B"))
    assert a is not None and b is not None
    assert a.frame_index == 0 and b.frame_index == 1


@pytest.mark.django_db
def test_record_many_sequential_frames(replay_track: m.ReplayTrack) -> None:
    r = ReplayRecorder(replay_track.id)
    frames = r.record_many(
        [
            _ev(key="x", event_type=et.EVENT_TYPE_DECODE_RAW_LOADED),
            _ev(key="y", event_type=et.EVENT_TYPE_DECODE_NORMALIZED),
        ]
    )
    assert [f.frame_index for f in frames] == [0, 1]


@pytest.mark.django_db
def test_cell_overlay_and_metrics_copied(replay_track: m.ReplayTrack) -> None:
    r = ReplayRecorder(replay_track.id)
    out = r.record_event(
        _ev(
            key="c",
            event_type=et.EVENT_TYPE_RECONSTRUCTION_BEGIN,
            overlay={"cells": [1]},
            metrics={"x": 2},
        )
    )
    assert out is not None
    assert out.cell_overlay_json == {"cells": [1]}
    assert out.metric_snapshot_json == {"x": 2}


@pytest.mark.django_db
def test_before_after_delta_preserved_in_frame_payload(replay_track: m.ReplayTrack) -> None:
    r = ReplayRecorder(replay_track.id)
    out = r.record_event(
        _ev(
            key="d",
            event_type=et.EVENT_TYPE_RECONSTRUCTION_BEGIN,
            before={"n": 0},
            after={"n": 1},
            delta={"dn": 1},
        )
    )
    assert out is not None
    assert out.frame_payload["before_state_json"] == {"n": 0}
    assert out.frame_payload["after_state_json"] == {"n": 1}
    assert out.frame_payload["delta_json"] == {"dn": 1}


@pytest.mark.django_db
def test_policy_capture_before_after_false_strips_state_payloads(
    replay_track: m.ReplayTrack,
) -> None:
    policy = ReplayRecordingPolicyDTO(capture_before_after=False)
    r = ReplayRecorder(replay_track.id, policy=policy)
    out = r.record_event(
        _ev(
            key="z",
            event_type=et.EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED,
            before={"a": 1},
            after={"b": 2},
            delta={"c": 3},
        )
    )
    assert out is not None
    assert out.frame_payload["before_state_json"] == {}
    assert out.frame_payload["after_state_json"] == {}
    assert out.frame_payload["delta_json"] == {}


@pytest.mark.django_db
def test_policy_max_frames_enforced(replay_track: m.ReplayTrack) -> None:
    r = ReplayRecorder(replay_track.id, policy=ReplayRecordingPolicyDTO(max_frames=1))
    r.record_event(_ev(key="a", event_type=et.EVENT_TYPE_DECODE_RAW_LOADED))
    with pytest.raises(ReplayRecorderCapExceeded):
        r.record_event(_ev(key="b", event_type=et.EVENT_TYPE_DECODE_NORMALIZED))


@pytest.mark.django_db
def test_policy_skips_candidate_rejected(replay_track: m.ReplayTrack) -> None:
    policy = ReplayRecordingPolicyDTO(capture_rejected_candidates=False)
    r = ReplayRecorder(replay_track.id, policy=policy)
    first = r.record_event(_ev(key="a", event_type=et.EVENT_TYPE_DECODE_RAW_LOADED))
    skipped = r.record_event(_ev(key="rej", event_type=et.EVENT_TYPE_CANDIDATE_REJECTED))
    third = r.record_event(_ev(key="b", event_type=et.EVENT_TYPE_DECODE_NORMALIZED))
    assert first is not None and skipped is None and third is not None
    assert third.frame_index == 1
    assert m.ReplayFrame.objects.filter(replay_track_id=replay_track.id).count() == 2


@pytest.mark.django_db
def test_invalid_event_type_rejected(replay_track: m.ReplayTrack) -> None:
    r = ReplayRecorder(replay_track.id)
    bad = SnapshotEventDTO(
        event_key="x",
        phase="p",
        event_type="custom.unknown",
        title="t",
    )
    with pytest.raises(ValueError, match="Unknown snapshot event_type"):
        r.record_event(bad)


def test_replay_recorder_only_imports_append_helpers_from_replay_service() -> None:
    import ast

    root = Path(__file__).resolve().parents[3]
    path = root / "django_apps" / "asteroid_lab" / "services" / "replay_recorder.py"
    mod = ast.parse(path.read_text(encoding="utf-8"))
    allowed = {"append_replay_frame", "next_replay_frame_index"}
    for node in mod.body:
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            if not node.module.endswith("replay_service"):
                continue
            got = {alias.name for alias in node.names}
            assert got <= allowed
