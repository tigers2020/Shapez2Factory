from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    SOLVER_FRAME_PASS3_TRANSPORT,
    SOLVER_FRAME_STEP4_ROUTING,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridor_read_factory import (  # noqa: E501
    protected_corridors_read_from_routing_state,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_corridors import (  # noqa: E501
    effective_routing_state_at_timeline_index,
    protected_corridors_overlay_from_routing_state,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_frames import (  # noqa: E501
    build_replay_ui_frames,
)


def test_overlay_flat_hard_wins_over_nested_protected_corridors() -> None:
    """Flat ``hard_protected_corridors`` is kept when nested ``protected_corridors.hard`` exists."""

    rs = {
        "hard_protected_corridors": [[9, 9]],
        "protected_corridors": {"hard": [[1, 2]], "soft": []},
    }
    o = protected_corridors_overlay_from_routing_state(rs)
    assert o["hard"] == [[9, 9]]
    assert o["counts"]["hard"] == 1
    dto = protected_corridors_read_from_routing_state(rs)
    assert dto.hard == {(9, 9)}


def test_protected_corridors_read_matches_overlay_cell_sets() -> None:
    rs = {
        "hard_protected_corridors": [[1, 2]],
        "soft_protected_corridors": [[3, 4]],
        "soft_protected_candidate_corridors": [[5, 6]],
    }
    o = protected_corridors_overlay_from_routing_state(rs)
    dto = protected_corridors_read_from_routing_state(rs)
    assert {(p[0], p[1]) for p in o["hard"]} == dto.hard
    assert {(p[0], p[1]) for p in o["soft"]} == dto.soft
    assert {(p[0], p[1]) for p in o["candidate"]} == dto.candidate


def test_protected_corridors_overlay_from_nested_routing_state() -> None:
    rs = {
        "protected_corridors": {
            "hard": [[2, 0]],
            "soft": [[3, 0], [4, 0]],
            "candidate": [[5, 0]],
        }
    }
    o = protected_corridors_overlay_from_routing_state(rs)
    assert o["counts"] == {"hard": 1, "soft": 2, "candidate": 1}
    assert o["hard"] == [[2, 0]]


def test_effective_routing_state_carries_forward_after_step4() -> None:
    rs = {"hard_protected_corridors": [[1, 0]], "soft_protected_corridors": [[2, 0]]}
    tl = [
        {"id": "solver_init", "summary": {}, "mining_map": []},
        {
            "id": SOLVER_FRAME_STEP4_ROUTING,
            "summary": {"routing_state": rs},
            "mining_map": [],
        },
        {"id": SOLVER_FRAME_PASS3_TRANSPORT, "summary": {}, "mining_map": []},
    ]
    assert effective_routing_state_at_timeline_index(tl, 2) == rs
    assert effective_routing_state_at_timeline_index(tl, 1) == rs


def test_build_replay_ui_frames_includes_protected_corridors_per_row() -> None:
    rs = {"hard_protected_corridors": [[9, 1]], "soft_protected_corridors": [[10, 1]]}
    tl = [
        {"id": "solver_init", "summary": {}, "mining_map": []},
        {
            "id": SOLVER_FRAME_STEP4_ROUTING,
            "summary": {"routing_state": rs},
            "mining_map": [],
        },
        {"id": SOLVER_FRAME_PASS3_TRANSPORT, "summary": {}, "mining_map": []},
    ]
    ui = build_replay_ui_frames(solver_timeline=tl, events=[])
    assert ui[0]["protected_corridors"]["counts"] == {"hard": 0, "soft": 0, "candidate": 0}
    assert ui[1]["protected_corridors"]["counts"]["hard"] == 1
    assert ui[2]["protected_corridors"]["counts"]["hard"] == 1
