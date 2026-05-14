"""§14 replay frame source: explicit counts and UI selection rule (display-only contract)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import solver_trace as st
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    enrich_solver_summary_replay_frame_contract,
)


def _enrich(d: dict, trace_on: bool) -> dict:
    with patch.object(st, "trace_enabled", return_value=trace_on):
        enrich_solver_summary_replay_frame_contract(d)
    return d


def test_replay_frame_source_replay_trace_when_cycle_frames() -> None:
    d = {
        "map_timeline_frame_count": 6,
        "solver_timeline_frame_count": 6,
        "replay_frame_count": 73,
        "replay_event_count": 731,
    }
    _enrich(d, trace_on=True)
    assert d["replay_frame_source"] == "replay_trace"
    assert d["replay_cycle_frame_count"] == 73
    assert d["decoded_map_timeline_frame_count"] == 6
    assert d["solver_milestone_frame_count"] == 6


def test_replay_frame_source_pass_snapshot_fallback_when_milestones_only() -> None:
    d = {
        "map_timeline_frame_count": 4,
        "solver_timeline_frame_count": 6,
        "replay_frame_count": 0,
        "replay_event_count": 0,
    }
    _enrich(d, trace_on=True)
    assert d["replay_frame_source"] == "pass_snapshot_fallback"
    assert d["replay_cycle_frame_count"] == 0


def test_replay_frame_source_map_timeline_only() -> None:
    d = {
        "map_timeline_frame_count": 6,
        "solver_timeline_frame_count": 0,
        "replay_frame_count": 0,
        "replay_event_count": 0,
    }
    _enrich(d, trace_on=True)
    assert d["replay_frame_source"] == "map_timeline_only"


def test_replay_frame_source_trace_disabled() -> None:
    d = {
        "map_timeline_frame_count": 6,
        "solver_timeline_frame_count": 6,
        "replay_frame_count": 73,
        "replay_event_count": 731,
    }
    _enrich(d, trace_on=False)
    assert d["replay_frame_source"] == "trace_disabled"


def test_enrich_exposes_four_distinct_counts() -> None:
    d = {
        "map_timeline_frame_count": 3,
        "solver_timeline_frame_count": 5,
        "replay_frame_count": 2,
        "replay_event_count": 40,
    }
    _enrich(d, trace_on=True)
    assert d["decoded_map_timeline_frame_count"] == 3
    assert d["solver_milestone_frame_count"] == 5
    assert d["replay_cycle_frame_count"] == 2
    assert d["replay_event_count"] == 40


def test_mining_layout_algorithm_tree_does_not_import_parse_replay_ndjson() -> None:
    """Replay NDJSON readers stay in ``solver_replay_ndjson`` / tests; not routing/placement."""

    root = Path("django_apps/shapez_asteroid/services/asteroid_mining_layout")
    skip = frozenset({"solver_trace.py", "solver_replay_ndjson.py"})
    bad: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if path.name in skip:
            continue
        text = path.read_text(encoding="utf-8")
        if "parse_replay_ndjson" in text:
            bad.append(str(path))
    assert not bad, "\n".join(bad)
