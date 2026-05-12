"""Unit tests for ``solver_replay_frames.build_replay_ui_frames``."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    RECOVERY_PHASE_VALIDATION_RECOVERY,
    SOLVER_FRAME_PASS2_INTERNAL,
    SOLVER_FRAME_PASS3_TRANSPORT,
    SOLVER_FRAME_STEP4_ROUTING,
    SOLVER_FRAME_VALIDATE,
    SOLVER_REPLAY_CONTRACT_VERSION,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    SolverMutationEventKind,
    build_solver_replay_snapshot,
    normalize_replay_transport_kind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_frames import (  # noqa: E501
    build_replay_ui_frames,
    verify_replay_ui_frames_computation_cycles,
)


def test_normalize_replay_transport_kind_aliases_and_passthrough() -> None:
    assert normalize_replay_transport_kind("belt") == "shape_belt"
    assert normalize_replay_transport_kind("Belt") == "shape_belt"
    assert normalize_replay_transport_kind("pipe") == "fluid_pipe"
    assert normalize_replay_transport_kind("shape_belt") == "shape_belt"
    assert normalize_replay_transport_kind("fluid_pipe") == "fluid_pipe"
    assert normalize_replay_transport_kind("Shape_Belt") == "shape_belt"
    assert normalize_replay_transport_kind("custom_tk") == "custom_tk"
    assert normalize_replay_transport_kind(None) is None
    assert normalize_replay_transport_kind("") is None
    assert normalize_replay_transport_kind("   ") is None


def test_build_replay_ui_frames_trunk_load_overlay_from_step4_summary() -> None:
    trunk_load = {
        "trunk_edge_load_observation": {
            "observation_version": 1,
            "top_n": 10,
            "shared_threshold": 2,
            "by_kind": {
                "shape_belt": {
                    "traversal_count_total": 2,
                    "max_sharing": 2,
                    "shared_edge_count": 1,
                    "edge_count": 1,
                    "top_edges": [{"edge": "1,0--2,0", "count": 2}],
                }
            },
        },
    }
    timeline = [
        {"id": SOLVER_FRAME_STEP4_ROUTING, "summary": {"trunk_load": trunk_load}, "mining_map": []},
        {"id": SOLVER_FRAME_PASS3_TRANSPORT, "summary": {}, "mining_map": []},
    ]
    frames = build_replay_ui_frames(solver_timeline=timeline, events=[])
    assert frames[0]["trunk_load_overlay"] is not None
    assert frames[0]["trunk_load_overlay"]["by_kind"]["shape_belt"]["max_sharing"] == 2
    assert frames[0]["trunk_load_overlay"].get("trunk_observation_layer") == "committed_step4_routes"
    assert frames[1]["trunk_load_overlay"] is not None
    assert verify_replay_ui_frames_computation_cycles(events=[], ui_frames=frames) == []


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
    assert frames[0]["computation_cycle_ui_tick_start"] == 1
    assert frames[0]["computation_cycle_ui_tick_end"] == 1
    assert frames[0]["primary_for_step10_ui"] is True
    assert frames[0]["overlay_event_indices"] == []
    assert frames[0]["pass3_layout_snapshots"] == []

    assert frames[1]["timeline_frame_id"] == SOLVER_FRAME_PASS3_TRANSPORT
    assert frames[1]["event_indices"] == [1, 2]
    assert frames[1]["computation_cycle_start"] == 4
    assert frames[1]["computation_cycle_end"] == 5
    assert frames[1]["computation_cycle_ui_tick_start"] == 1
    assert frames[1]["computation_cycle_ui_tick_end"] == 1
    assert frames[1]["primary_for_step10_ui"] is True
    assert frames[1]["overlay_event_indices"] == []
    snaps = frames[1]["pass3_layout_snapshots"]
    assert len(snaps) == 2
    assert snaps[0]["marker"] == "before"
    assert snaps[0]["layout_state_sha256"] == "abc"
    assert snaps[1]["marker"] == "after"
    assert verify_replay_ui_frames_computation_cycles(events=events, ui_frames=frames) == []


def test_build_replay_ui_frames_overlay_indices_per_phase() -> None:
    """Overlay kinds attach to the frame whose phase map includes the event (step4 vs pass3/p4)."""

    timeline = [
        {"id": SOLVER_FRAME_STEP4_ROUTING, "summary": {}, "mining_map": []},
        {"id": SOLVER_FRAME_PASS3_TRANSPORT, "summary": {}, "mining_map": []},
    ]
    events: list[dict] = [
        {"phase": "step4", "kind": SolverMutationEventKind.MAP_DIFF_COMMITTED.value},
        {
            "phase": "step4",
            "kind": SolverMutationEventKind.ROUTE_REPLACED.value,
            "payload": {"cascade_reroute_count": 2},
        },
        {
            "phase": "pass3",
            "kind": SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value,
            "payload": {
                "marker": "before",
                "layout_state_sha256": "abc",
                "transaction_id": "p3",
            },
        },
        {"phase": "pass3", "kind": SolverMutationEventKind.ROLLBACK.value, "payload": {}},
        {
            "phase": "p4_reclaim",
            "kind": SolverMutationEventKind.RECOVERY_BRANCH.value,
            "payload": {"validation_recovery_attempt": 1},
        },
    ]
    frames = build_replay_ui_frames(solver_timeline=timeline, events=events)
    assert frames[0]["event_indices"] == [0, 1]
    assert frames[0]["overlay_event_indices"] == [1]
    assert events[frames[0]["overlay_event_indices"][0]]["kind"] == (
        SolverMutationEventKind.ROUTE_REPLACED.value
    )

    assert frames[1]["event_indices"] == [2, 3, 4]
    assert frames[1]["overlay_event_indices"] == [3, 4]
    kinds_p3 = {events[i]["kind"] for i in frames[1]["overlay_event_indices"]}
    assert SolverMutationEventKind.ROLLBACK.value in kinds_p3
    assert SolverMutationEventKind.RECOVERY_BRANCH.value in kinds_p3


def test_build_replay_ui_frames_maps_validation_recovery_events() -> None:
    """Orchestrator phase ``validation_recovery`` maps to the validate timeline frame."""

    timeline = [
        {"id": SOLVER_FRAME_PASS2_INTERNAL, "summary": {}, "mining_map": []},
        {"id": SOLVER_FRAME_PASS3_TRANSPORT, "summary": {}, "mining_map": []},
        {"id": SOLVER_FRAME_VALIDATE, "summary": {}, "mining_map": []},
    ]
    events: list[dict] = [
        {
            "phase": "pass12",
            "kind": SolverMutationEventKind.TRANSACTION_BEGIN.value,
        },
        {
            "phase": RECOVERY_PHASE_VALIDATION_RECOVERY,
            "kind": SolverMutationEventKind.FRAME_CHECKPOINT.value,
            "payload": {"validation_recovery_attempt": 0},
        },
    ]
    frames = build_replay_ui_frames(solver_timeline=timeline, events=events)
    assert frames[2]["timeline_frame_id"] == SOLVER_FRAME_VALIDATE
    assert frames[2]["event_indices"] == [1]


def test_build_replay_ui_frames_recovery_branch_event_indices_visible() -> None:
    """``recovery_branch`` + ``phase=validation_recovery`` appears on validate row overlays."""

    timeline = [
        {"id": SOLVER_FRAME_PASS3_TRANSPORT, "summary": {}, "mining_map": []},
        {"id": SOLVER_FRAME_VALIDATE, "summary": {}, "mining_map": []},
    ]
    events: list[dict] = [
        {
            "phase": "pass3",
            "kind": SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value,
            "payload": {
                "marker": "before",
                "layout_state_sha256": "aaa",
                "transaction_id": "t",
            },
        },
        {
            "phase": RECOVERY_PHASE_VALIDATION_RECOVERY,
            "kind": SolverMutationEventKind.RECOVERY_BRANCH.value,
            "payload": {"validation_recovery_attempt": 1},
        },
    ]
    frames = build_replay_ui_frames(solver_timeline=timeline, events=events)
    validate_row = frames[1]
    assert validate_row["timeline_frame_id"] == SOLVER_FRAME_VALIDATE
    assert validate_row["event_indices"] == [1]
    assert validate_row["overlay_event_indices"] == [1]
    assert (
        events[validate_row["overlay_event_indices"][0]]["kind"]
        == SolverMutationEventKind.RECOVERY_BRANCH.value
    )


def test_route_replaced_v5_cells_on_step4_frame_from_payload() -> None:
    """v5 ``route_replaced`` may carry aggregate ``cells_*`` on the event (STEP4 overlay)."""

    timeline = [
        {"id": SOLVER_FRAME_STEP4_ROUTING, "summary": {}, "mining_map": []},
    ]
    events: list[dict] = [
        {
            "phase": "step4",
            "kind": SolverMutationEventKind.ROUTE_REPLACED.value,
            "payload": {
                "cascade_reroute_count": 1,
                "cells_removed": [[5, 1]],
                "cells_added": [[7, 1]],
                "cells_kept": None,
                "transport_kind": "shape_belt",
                "replacement_reason": "p2c_cascade_reroute",
                "transaction_id": "abc",
            },
        },
    ]
    frames = build_replay_ui_frames(solver_timeline=timeline, events=events)
    assert frames[0]["event_indices"] == [0]
    assert frames[0]["overlay_event_indices"] == [0]
    pl = events[frames[0]["overlay_event_indices"][0]]["payload"]
    assert pl["cells_removed"] == [[5, 1]]
    assert pl["cells_added"] == [[7, 1]]


def test_route_replaced_v5_payload_accepts_belt_alias_transport_kind() -> None:
    """Frame builder tolerates legacy ``belt`` in payload (normalization is emitter-side)."""

    timeline = [
        {"id": SOLVER_FRAME_STEP4_ROUTING, "summary": {}, "mining_map": []},
    ]
    events: list[dict] = [
        {
            "phase": "step4",
            "kind": SolverMutationEventKind.ROUTE_REPLACED.value,
            "payload": {
                "cascade_reroute_count": 1,
                "cells_removed": [[5, 1]],
                "cells_added": [[7, 1]],
                "transport_kind": "belt",
                "transaction_id": "abc",
            },
        },
    ]
    frames = build_replay_ui_frames(solver_timeline=timeline, events=events)
    assert frames[0]["overlay_event_indices"] == [0]


def test_build_solver_replay_snapshot_includes_ui_frames_contract_v5() -> None:
    timeline = [
        {"id": SOLVER_FRAME_PASS2_INTERNAL, "summary": {}, "mining_map": []},
        {"id": SOLVER_FRAME_PASS3_TRANSPORT, "summary": {}, "mining_map": []},
    ]
    events: list[dict] = [
        {
            "phase": "pass12",
            "kind": SolverMutationEventKind.TRANSACTION_BEGIN.value,
            "payload": {},
        },
    ]
    snap = build_solver_replay_snapshot(frames=timeline, run_id="r1", events=events)
    assert snap["contract_version"] == SOLVER_REPLAY_CONTRACT_VERSION
    assert snap["contract_version"] >= 5
    assert "ui_frames" in snap
    assert isinstance(snap["ui_frames"], list)
    assert len(snap["ui_frames"]) == len(timeline)
    assert verify_replay_ui_frames_computation_cycles(
        events=snap["events"], ui_frames=snap["ui_frames"]
    ) == []


def test_verify_replay_ui_frames_computation_cycles_detects_mismatched_bounds() -> None:
    events: list[dict] = [
        {"phase": "x", "computation_cycle": 1},
        {"phase": "x", "computation_cycle": 2},
    ]
    bad_row = {
        "timeline_index": 0,
        "event_indices": [0, 1],
        "computation_cycle_start": 1,
        "computation_cycle_end": 99,
    }
    errs = verify_replay_ui_frames_computation_cycles(events=events, ui_frames=[bad_row])
    assert errs and "99" in errs[0]
