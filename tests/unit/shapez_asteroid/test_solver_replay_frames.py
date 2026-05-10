"""Unit tests for ``solver_replay_frames.build_replay_ui_frames``."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    SOLVER_FRAME_PASS2_INTERNAL,
    SOLVER_FRAME_PASS3_TRANSPORT,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    SolverMutationEventKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_frames import (  # noqa: E501
    build_replay_ui_frames,
)


def test_build_replay_ui_frames_pass3_snapshots_attached_to_pass3_frame() -> None:
    timeline = [
        {"id": SOLVER_FRAME_PASS2_INTERNAL, "summary": {}, "mining_map": []},
        {"id": SOLVER_FRAME_PASS3_TRANSPORT, "summary": {}, "mining_map": []},
    ]
    events: list[dict] = [
        {
            "phase": "pass12",
            "kind": SolverMutationEventKind.TRANSACTION_BEGIN.value,
            "computation_cycle": 1,
            "payload": {"transaction_id": "p12"},
        },
        {
            "phase": "pass3",
            "kind": SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value,
            "computation_cycle": 4,
            "payload": {
                "marker": "before",
                "layout_state_sha256": "abc",
                "transaction_id": "p3",
            },
        },
        {
            "phase": "pass3",
            "kind": SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value,
            "computation_cycle": 5,
            "payload": {
                "marker": "after",
                "layout_state_sha256": "def",
                "transaction_id": "p3",
            },
        },
    ]
    frames = build_replay_ui_frames(solver_timeline=timeline, events=events)
    assert len(frames) == 2
    assert frames[0]["timeline_frame_id"] == SOLVER_FRAME_PASS2_INTERNAL
    assert frames[0]["event_indices"] == [0]
    assert frames[0]["computation_cycle_start"] == 1
    assert frames[0]["computation_cycle_end"] == 1
    assert frames[0]["pass3_layout_snapshots"] == []

    assert frames[1]["timeline_frame_id"] == SOLVER_FRAME_PASS3_TRANSPORT
    assert frames[1]["event_indices"] == [1, 2]
    assert frames[1]["computation_cycle_start"] == 4
    assert frames[1]["computation_cycle_end"] == 5
    snaps = frames[1]["pass3_layout_snapshots"]
    assert len(snaps) == 2
    assert snaps[0]["marker"] == "before"
    assert snaps[0]["layout_state_sha256"] == "abc"
    assert snaps[1]["marker"] == "after"
