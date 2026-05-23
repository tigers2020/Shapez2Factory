"""RTTP replay sink — null and in-memory implementations."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.replay_sink import (
    InMemoryRttpReplaySink,
    NullRttpReplaySink,
    resolve_replay_sink,
)
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO


def _event() -> SnapshotEventDTO:
    return SnapshotEventDTO(
        event_key="k1",
        phase="rttp_pipeline",
        event_type=et.EVENT_TYPE_ROUTING_PROBE_STARTED,
        title="t",
    )


def test_null_sink_drops_events() -> None:
    sink = NullRttpReplaySink()
    out = sink.record(_event())
    assert out is None


def test_in_memory_sink_appends() -> None:
    sink = InMemoryRttpReplaySink()
    ev = _event()
    sink.record(ev)
    assert len(sink.events) == 1
    assert sink.events[0] is ev


def test_resolve_replay_sink_none_is_null() -> None:
    sink = resolve_replay_sink(None)
    assert isinstance(sink, NullRttpReplaySink)
