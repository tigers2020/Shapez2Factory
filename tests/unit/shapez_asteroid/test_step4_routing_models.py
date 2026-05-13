"""STEP4 internal routing DTO builders."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    _build_step4_ctx_state,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_models import (
    Step4GoalSet,
    Step4RouteAttemptResult,
    Step4RouteJob,
    Step4StubRouteJob,
)


def test_step4_goal_set_from_merge_round() -> None:
    meta = {
        "applied": True,
        "mode": "trunk_manhattan_margin_lex",
        "priority_head": ([1, 2], [3, 4]),
    }
    gs = Step4GoalSet.from_merge_round(
        raw_goal={(0, 0)},
        merged_union_cells=frozenset({(0, 0), (5, 5)}),
        goal_order_meta=meta,
        fluid_primary_goal_cells=frozenset({(5, 5)}),
    )
    assert gs.raw_goal_cells == frozenset({(0, 0)})
    assert gs.merged_union_cells == frozenset({(0, 0), (5, 5)})
    assert gs.goal_ordering_mode == "trunk_manhattan_margin_lex"
    assert gs.merge_applied is True
    assert gs.priority_head == ((1, 2), (3, 4))
    assert gs.fluid_primary_goal_cells == frozenset({(5, 5)})


def test_step4_route_job_as_stub() -> None:
    rj = Step4RouteJob(
        extractor_cell=(1, 1),
        stub_cell=(2, 2),
        transport_kind="fluid_pipe",
        placement_id="p1",
        job_seq=3,
        placement_commit_state_at_route_attempt="provisional_placed",
    )
    st = rj.as_stub_job()
    assert isinstance(st, Step4StubRouteJob)
    assert st.placement_id == "p1"
    assert st.stub_cell == (2, 2)
    assert rj.job_seq == 3


def test_step4_route_attempt_result_capture_is_readonly() -> None:
    d = {"stop_reason": "exhausted", "expanded_nodes": 1}
    ar = Step4RouteAttemptResult.capture(None, d)
    assert ar.path is None
    assert ar.search_stats["expanded_nodes"] == 1
    d["expanded_nodes"] = 99
    assert ar.search_stats["expanded_nodes"] == 1


def _minimal_map() -> list[dict]:
    return [
        {
            "x": 1,
            "y": 1,
            "role": "occupied",
            "layout_kind": "asteroid_field",
        },
    ]


def test_build_step4_ctx_state_empty_jobs() -> None:
    final_map = _minimal_map()
    ctx, state = _build_step4_ctx_state(
        _minimal_map(),
        final_mining_map=final_map,
        is_external=lambda c: c[0] <= 0,
        placement_records=None,
        existing_layout_analysis=None,
        hard_protected_cells=None,
        force_route_attempt_placement_ids=None,
    )
    assert ctx.mineable == frozenset({(1, 1)})
    assert state.jobs == []
    assert state.cells.keys() == {(1, 1)}
