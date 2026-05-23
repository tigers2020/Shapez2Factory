"""RTTP DbRttpReplaySink — persists registered events to ReplayFrame."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.replay_sink import DbRttpReplaySink
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO

pytestmark = pytest.mark.django_db


@pytest.fixture
def replay_track() -> m.ReplayTrack:
    project = m.AsteroidProject.objects.create(name="DbSink", slug="db-sink-proj")
    return m.ReplayTrack.objects.create(project=project, track_key="db-sink-track")


def _event() -> SnapshotEventDTO:
    return SnapshotEventDTO(
        event_key="k1",
        phase="rttp_pipeline",
        event_type=et.EVENT_TYPE_ROUTING_PROBE_STARTED,
        title="t",
        is_decision_point=True,
    )


def test_db_replay_sink_persists_registered_event(replay_track: m.ReplayTrack) -> None:
    sink = DbRttpReplaySink(replay_track.id)
    sink.record(_event())
    assert m.ReplayFrame.objects.filter(replay_track_id=replay_track.id).count() == 1


def test_db_replay_sink_record_return_is_passthrough(replay_track: m.ReplayTrack) -> None:
    sink = DbRttpReplaySink(replay_track.id)
    out = sink.record(_event())
    assert out is not None
    assert getattr(out, "replay_frame_id", None) is not None
