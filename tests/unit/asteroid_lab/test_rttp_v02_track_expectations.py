"""H2 — RTTP v0.2 Lab vs optimization replay track expectations.

PR-B persistence proof:
  - ``ReplayTrack`` with ``track_key == rttp_optimization_track_key(run_key)`` (``{run_key}:rttp``)
  - ``ReplayFrame`` count >= 4 with RTTP pipeline milestone ``event_type`` values

Lab product timeline (until Sequence 3B UI compose):
  - ``lab_replay_frames_json`` = inspection / reconstruction only
  - MUST NOT assert RTTP milestone ``event_type`` values appear in Lab JSON
  - MUST assert Lab JSON event types are disjoint from RTTP milestones (integration smoke)

See:
  - ``docs/superpowers/specs/2026-05-23-rttp-v0.2-replay-parity-design.md`` (H2)
  - ``tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py``
"""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.replay_track_keys import (
    RTTP_OPTIMIZATION_TRACK_SUFFIX,
    rttp_optimization_track_key,
)
from tests.support.rttp_v02_contract import RTTP_PIPELINE_MILESTONE_EVENT_TYPES


def test_rttp_optimization_track_key_suffix() -> None:
    assert rttp_optimization_track_key("my-run") == f"my-run{RTTP_OPTIMIZATION_TRACK_SUFFIX}"


def test_rttp_pipeline_milestone_event_types_are_registered() -> None:
    from django_apps.asteroid_lab.replay.event_types import SNAPSHOT_EVENT_TYPES

    assert RTTP_PIPELINE_MILESTONE_EVENT_TYPES <= SNAPSHOT_EVENT_TYPES
