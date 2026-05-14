from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.replay.snapshots import (
    LayoutSnapshot,
    read_ndjson_replay_events,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.replay.trace_event import (
    TraceEvent,
)


def test_trace_event_is_mutable_output_container() -> None:
    ev = TraceEvent(run_id="r", phase="p", step_index=0, event_type="t")
    ev.data["k"] = 1
    assert ev.data["k"] == 1


def test_layout_snapshot_frozen() -> None:
    snap = LayoutSnapshot(phase="after_pass1", cells=frozenset({(1, 1)}))
    assert snap.phase == "after_pass1"


def test_ndjson_reader_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        next(read_ndjson_replay_events("dummy.ndjson"))
