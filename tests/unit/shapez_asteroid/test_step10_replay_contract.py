"""STEP10 replay/trace contract: schema, Pass3 snapshots, no algorithm reads of replay output."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    SOLVER_REPLAY_CONTRACT_VERSION,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    solver_replay_events as _sre,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    _pass3_summary_for_solver_timeline,
)


def test_prepare_replay_events_sets_schema_and_stream_tick_at_cycle_10() -> None:
    events: list[dict] = [{"kind": "frame_checkpoint", "phase": "step4", "payload": {}}]
    for _ in range(8):
        events.append({"kind": "frame_checkpoint", "phase": "step4", "payload": {}})
    events.append(
        {
            "kind": _sre.SolverMutationEventKind.RECOVERY_BRANCH.value,
            "phase": "validation_recovery",
            "payload": {"recovery_trigger": "validation_recovery_entry"},
        }
    )
    _sre.prepare_replay_events_for_snapshot(events)
    assert events[9]["computation_cycle"] == 10
    assert events[9]["visualization_stream_tick"] is True
    assert events[0]["visualization_stream_tick"] is False
    assert events[9]["recovery_trigger"] == "validation_recovery_entry"
    for ev in events:
        assert isinstance(ev, dict)
        for k in _sre.REPLAY_EVENT_TRACE_OPTIONAL_KEYS:
            assert k in ev


def test_build_solver_replay_snapshot_pass3_snapshot_refs_and_overlay() -> None:
    tid = "abc123"
    events = [
        {
            "kind": _sre.SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value,
            "phase": "pass3",
            "payload": {
                "marker": "before",
                "layout_state_sha256": "aa",
                "transaction_id": tid,
            },
        },
        {
            "kind": _sre.SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value,
            "phase": "pass3",
            "payload": {
                "marker": "after",
                "layout_state_sha256": "bb",
                "transaction_id": tid,
            },
        },
    ]
    ela = {
        "transport": {
            "components": [
                {"status": "main_trunk_candidate", "cells": [[1, 1], [2, 1]]},
                {"status": "orphan_component", "cells": [[9, 9]]},
            ]
        },
        "equipment": {
            "miners_without_adjacent_transport": [[3, 3]],
            "miners_attached_to_orphan_transport": [],
        },
        "issues": [{"code": "X", "severity": "warning", "coords": [[4, 4]]}],
    }
    snap = _sre.build_solver_replay_snapshot(
        frames=[{"id": "solver_init", "summary": {"step": "init"}, "mining_map": []}],
        run_id="r-step10",
        events=events,
        existing_layout_analysis=ela,
        placement_recovery_overlay={
            "step4_rolled_back_placement_ids": ["p1"],
            "step4_quarantined_placement_ids": [],
        },
    )
    assert snap["contract_version"] == SOLVER_REPLAY_CONTRACT_VERSION
    assert snap["layout_snapshot_before_pass3"]["layout_state_sha256"] == "aa"
    assert snap["layout_snapshot_after_pass3"]["layout_state_sha256"] == "bb"
    ov = snap["existing_layout_replay_overlay"]
    assert ov["original_main_trunk_component"] == [[1, 1], [2, 1]]
    assert [9, 9] in ov["original_orphan_transport_components"]
    assert snap["placement_recovery_overlay"]["step4_rolled_back_placement_ids"] == ["p1"]


def test_existing_layout_replay_overlay_none_for_missing_analysis() -> None:
    assert _sre.existing_layout_replay_overlay(None) is None


def test_pass3_timeline_summary_clears_commit_reason_when_not_final_committed() -> None:
    s = _pass3_summary_for_solver_timeline(
        {"pass3_final_committed": False, "pass3_commit_reason": "normal_gain", "pass3_gain": 0}
    )
    assert s["pass3_commit_reason"] is None
    s2 = _pass3_summary_for_solver_timeline(
        {
            "pass3_final_committed": True,
            "pass3_commit_reason": "normal_gain",
            "pass3_gain": 1,
        }
    )
    assert s2["pass3_commit_reason"] == "normal_gain"


def test_build_solver_timeline_replay_has_step10_root_fields() -> None:
    decoded: dict = {
        "BP": {
            "Entries": [{"X": x, "Y": 0, "T": "Layout_ShapeMiner"} for x in range(10, 13)]
            + [{"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0} for x in range(13, 30)]
        }
    }
    out = build_solver_timeline(decoded)
    sr = out["solver_replay"]
    ss = out.get("solver_summary") or {}
    assert isinstance(ss.get("solver_timeline_frame_count"), int)
    assert isinstance(ss.get("map_timeline_frame_count"), int)
    assert "replay_frame_count" in ss and "replay_event_count" in ss
    assert ss.get("decoded_map_timeline_frame_count") == ss.get("map_timeline_frame_count")
    assert ss.get("solver_milestone_frame_count") == ss.get("solver_timeline_frame_count")
    assert ss.get("replay_cycle_frame_count") == ss.get("replay_frame_count")
    assert ss.get("replay_frame_source") in (
        "replay_trace",
        "pass_snapshot_fallback",
        "map_timeline_only",
        "trace_disabled",
    )
    assert "layout_snapshot_before_pass3" in sr
    assert "layout_snapshot_after_pass3" in sr
    assert sr["layout_snapshot_before_pass3"] is not None
    assert sr["layout_snapshot_after_pass3"] is not None
    assert "placement_recovery_overlay" in sr
    assert isinstance(sr["placement_recovery_overlay"], dict)
    assert isinstance(sr.get("cycle_frames"), list)
    assert isinstance(sr.get("ui_frames"), list)


@pytest.mark.parametrize(
    "rel",
    [
        "pass3/pass3_greedy_core.py",
        "pass3/pass3_transport.py",
        "step4/step4_merge_routing.py",
    ],
)
def test_core_algorithm_files_do_not_read_replay_events_list(rel: str) -> None:
    root = Path("django_apps/shapez_asteroid/services/asteroid_mining_layout")
    text = (root / rel).read_text(encoding="utf-8")
    assert "replay_events" not in text, f"{rel} must not reference replay_events (output-only)"
