"""``replay_service`` — append, payload ordering, playback upsert."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services import replay_service
from django_apps.asteroid_lab.services.dto import (
    PlaybackPatchDTO,
    ReplayFrameAppendDTO,
    ReplayFrameDTO,
)


@pytest.fixture
def replay_track() -> m.ReplayTrack:
    p = m.AsteroidProject.objects.create(name="R", slug="r-svc")
    return m.ReplayTrack.objects.create(project=p, track_key="t1")


def test_replay_frame_dto_alias_matches_append_dto() -> None:
    assert ReplayFrameDTO is ReplayFrameAppendDTO


@pytest.mark.django_db
def test_append_replay_frame_monotonic_auto_index(replay_track: m.ReplayTrack) -> None:
    a = ReplayFrameAppendDTO(frame_key="a", phase="p", title="A")
    b = ReplayFrameAppendDTO(frame_key="b", phase="p", title="B")
    ra = replay_service.append_replay_frame(replay_track.id, a)
    rb = replay_service.append_replay_frame(replay_track.id, b)
    assert ra.frame_index == 0
    assert rb.frame_index == 1


@pytest.mark.django_db
def test_append_replay_frame_explicit_index_must_match_next(replay_track: m.ReplayTrack) -> None:
    replay_service.append_replay_frame(
        replay_track.id,
        ReplayFrameAppendDTO(frame_key="a", phase="p", title="A", frame_index=0),
    )
    replay_service.append_replay_frame(
        replay_track.id,
        ReplayFrameAppendDTO(frame_key="b", phase="p", title="B", frame_index=1),
    )
    with pytest.raises(ValueError, match="monotonic"):
        replay_service.append_replay_frame(
            replay_track.id,
            ReplayFrameAppendDTO(frame_key="c", phase="p", title="C", frame_index=3),
        )


@pytest.mark.django_db
def test_get_replay_track_payload_order_and_metric_overlay(replay_track: m.ReplayTrack) -> None:
    m.ReplayFrame.objects.create(
        replay_track=replay_track,
        frame_index=1,
        frame_key="late",
        phase="p",
        title="second",
        metric_snapshot_json={"fitness": 0.5},
    )
    m.ReplayFrame.objects.create(
        replay_track=replay_track,
        frame_index=0,
        frame_key="early",
        phase="p",
        title="first",
        metric_snapshot_json={"fitness": 0.1},
    )
    payload = replay_service.get_replay_track_payload(replay_track.id)
    assert [f.frame_index for f in payload.frames] == [0, 1]
    assert payload.frames[1].metric_snapshot_json == {"fitness": 0.5}


@pytest.mark.django_db
def test_update_playback_session_upsert(replay_track: m.ReplayTrack) -> None:
    dto = replay_service.update_playback_session(
        replay_track.id,
        PlaybackPatchDTO(current_frame_index=2, is_playing=True, ui_state_json={"zoom": 1.2}),
    )
    assert dto.replay_track_id == replay_track.id
    assert dto.current_frame_index == 2
    assert dto.is_playing is True
    assert dto.ui_state_json["zoom"] == pytest.approx(1.2)

    dto2 = replay_service.update_playback_session(
        replay_track.id,
        PlaybackPatchDTO(ui_state_json={"pan": 3}),
    )
    assert dto2.ui_state_json["zoom"] == pytest.approx(1.2)
    assert dto2.ui_state_json["pan"] == 3


@pytest.mark.django_db
def test_update_playback_session_idempotent_single_row(replay_track: m.ReplayTrack) -> None:
    """``UIPlaybackSession`` is one-to-one with ``ReplayTrack`` — no duplicate rows per track."""

    replay_service.update_playback_session(
        replay_track.id,
        PlaybackPatchDTO(current_frame_index=1),
    )
    replay_service.update_playback_session(
        replay_track.id,
        PlaybackPatchDTO(current_frame_index=2),
    )
    assert m.UIPlaybackSession.objects.filter(replay_track_id=replay_track.id).count() == 1
    s = m.UIPlaybackSession.objects.get(replay_track_id=replay_track.id)
    assert s.current_frame_index == 2
