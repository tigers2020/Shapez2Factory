"""Replay NDJSON helpers are output/tooling only (§16), not algorithm inputs."""

from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.replay.snapshots import (
    read_ndjson_replay_events,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.replay.trace_event import (
    TraceEvent,
)


def test_read_ndjson_replay_events_is_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        next(read_ndjson_replay_events("dummy.ndjson"))


def test_trace_event_dataclass_instantiable() -> None:
    ev = TraceEvent(
        run_id="r",
        phase="p",
        step_index=0,
        event_type="noop",
    )
    assert ev.run_id == "r"
    assert ev.data == {}
