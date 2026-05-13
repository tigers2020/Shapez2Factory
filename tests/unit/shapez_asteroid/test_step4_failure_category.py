"""STEP4 stub-local failure taxonomy (telemetry-only mapping)."""

from __future__ import annotations

import json
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_failure_category as _s4fc,
)


def test_classify_geometry_cage_neighbor_mix() -> None:
    stub: Coord = (5, 5)
    near: list[dict[str, Any]] = [
        {"cell": [5, 6], "reason": "blocked"},
        {"cell": [6, 5], "reason": "blocked"},
        {"cell": [4, 5], "reason": "step_cost_none"},
        {"cell": [5, 4], "reason": "step_cost_none"},
    ]
    cat = _s4fc.classify_step4_failure_category(
        stop_reason="exhausted",
        last_error="no_route_exhausted",
        nearest_transport_hops=3,
        near=near,
        goal_cells_count=2,
        reachable_goal_count=1,
        cells={},
        want_role="belt",
        stub_cell=stub,
        hard_extras=frozenset(),
    )
    assert cat == _s4fc.Step4FailureCategory.geometry_cage.value


def test_classify_no_same_kind_trunk() -> None:
    stub: Coord = (0, 0)
    near: list[dict[str, Any]] = [
        {"cell": [0, 1], "reason": "ok"},
        {"cell": [1, 0], "reason": "ok"},
        {"cell": [-1, 0], "reason": "blocked"},
        {"cell": [0, -1], "reason": "blocked"},
    ]
    cat = _s4fc.classify_step4_failure_category(
        stop_reason="exhausted",
        last_error="no_route_exhausted",
        nearest_transport_hops=None,
        near=near,
        goal_cells_count=1,
        reachable_goal_count=0,
        cells={},
        want_role="belt",
        stub_cell=stub,
        hard_extras=frozenset(),
    )
    assert cat == _s4fc.Step4FailureCategory.no_same_kind_trunk.value


def test_classify_search_budget_exhausted() -> None:
    stub: Coord = (1, 1)
    near: list[dict[str, Any]] = [{"cell": [1, 2], "reason": "ok"}]
    cat = _s4fc.classify_step4_failure_category(
        stop_reason="budget",
        last_error="no_route_budget",
        nearest_transport_hops=1,
        near=near,
        goal_cells_count=1,
        reachable_goal_count=0,
        cells={},
        want_role="belt",
        stub_cell=stub,
        hard_extras=frozenset(),
    )
    assert cat == _s4fc.Step4FailureCategory.search_budget_exhausted.value


def test_classify_orphan_merge_forbidden_adjacent_pipe() -> None:
    stub: Coord = (2, 2)
    adj: Coord = (2, 3)
    near: list[dict[str, Any]] = [
        {"cell": [int(adj[0]), int(adj[1])], "reason": "ok"},
        {"cell": [3, 2], "reason": "ok"},
        {"cell": [1, 2], "reason": "ok"},
        {"cell": [2, 1], "reason": "ok"},
    ]
    cells = {adj: {"role": "pipe", "surface": "fluid"}}
    cat = _s4fc.classify_step4_failure_category(
        stop_reason="exhausted",
        last_error="no_route_exhausted",
        nearest_transport_hops=2,
        near=near,
        goal_cells_count=1,
        reachable_goal_count=0,
        cells=cells,
        want_role="belt",
        stub_cell=stub,
        hard_extras=frozenset(),
    )
    assert cat == _s4fc.Step4FailureCategory.orphan_merge_forbidden.value


def test_protected_corridor_hard_involved_neighbor_reason() -> None:
    stub: Coord = (0, 0)
    near = [{"cell": [0, 1], "reason": "hard_protected"}]
    assert (
        _s4fc.protected_corridor_hard_involved(near, stub_cell=stub, hard_extras=frozenset())
        is True
    )


def test_build_step4_failure_classification_json_stable() -> None:
    sub = _s4fc.build_step4_failure_classification_dict(
        category="goal_starvation",
        confidence="medium",
        evidence={
            "route_goal_set_size": 3,
            "reachable_goal_count": 0,
            "frontier_stop_reason": "exhausted",
            "search_budget_exhausted": False,
            "blocked_neighbor_counts": {"blocked": 2, "ok": 2},
        },
    )
    s1 = json.dumps(sub, sort_keys=True)
    s2 = json.dumps(sub, sort_keys=True)
    assert s1 == s2
    assert sub["category"] == "goal_starvation"
    assert sub["confidence"] == "medium"
    assert sub["evidence"]["reachable_goal_count"] == 0


def test_t3_goal_starvation_exhausted_unreachable_goals() -> None:
    stub: Coord = (0, 0)
    near = [
        {"cell": [0, 1], "reason": "ok"},
        {"cell": [1, 0], "reason": "ok"},
        {"cell": [-1, 0], "reason": "blocked"},
        {"cell": [0, -1], "reason": "blocked"},
    ]
    cat, conf, ev = _s4fc.compute_step4_failure_classification(
        stop_reason="exhausted",
        last_error="no_route_exhausted",
        nearest_transport_hops=2,
        near=near,
        goal_cells_count=2,
        reachable_goal_count=0,
        cells={},
        want_role="belt",
        stub_cell=stub,
        hard_extras=frozenset(),
        goal_cells=frozenset({(5, 5), (6, 6)}),
        frontier_stop_reason="exhausted",
        existing_trunk_present=False,
        existing_trunk_goal_count=0,
        reachable_existing_trunk_count=0,
        reachable_exterior_margin_count=0,
        search_budget_exhausted=False,
        expanded_nodes=10,
    )
    assert cat == _s4fc.Step4FailureCategory.goal_starvation.value
    assert conf == "medium"
    assert ev["reachable_goal_count"] == 0


def test_t3_merge_starvation_trunk_goals_unreachable() -> None:
    stub: Coord = (1, 1)
    near = [
        {"cell": [0, 1], "reason": "ok"},
        {"cell": [1, 0], "reason": "blocked"},
        {"cell": [2, 1], "reason": "blocked"},
        {"cell": [1, 2], "reason": "blocked"},
    ]
    cat, conf, _ = _s4fc.compute_step4_failure_classification(
        stop_reason="exhausted",
        last_error="no_route_exhausted",
        nearest_transport_hops=3,
        near=near,
        goal_cells_count=3,
        reachable_goal_count=0,
        cells={},
        want_role="belt",
        stub_cell=stub,
        hard_extras=frozenset(),
        goal_cells=frozenset({(9, 9)}),
        frontier_stop_reason="exhausted",
        existing_trunk_present=True,
        existing_trunk_goal_count=1,
        reachable_existing_trunk_count=0,
        reachable_exterior_margin_count=0,
        search_budget_exhausted=False,
        expanded_nodes=12,
    )
    assert cat == _s4fc.Step4FailureCategory.merge_starvation.value
    assert conf == "medium"


def test_t3_search_budget_exhausted_frontier_budget() -> None:
    stub: Coord = (0, 0)
    near = [{"cell": [0, 1], "reason": "ok"}]
    cat, conf, ev = _s4fc.compute_step4_failure_classification(
        stop_reason="budget",
        last_error="no_route_budget",
        nearest_transport_hops=1,
        near=near,
        goal_cells_count=1,
        reachable_goal_count=0,
        cells={},
        want_role="belt",
        stub_cell=stub,
        hard_extras=frozenset(),
        frontier_stop_reason="budget",
        search_budget_exhausted=True,
    )
    assert cat == _s4fc.Step4FailureCategory.search_budget_exhausted.value
    assert conf == "high"
    assert ev["search_budget_exhausted"] is True


def test_t3_stub_isolated_four_blocked_neighbors() -> None:
    stub: Coord = (0, 0)
    near = [
        {"cell": [0, 1], "reason": "blocked"},
        {"cell": [1, 0], "reason": "blocked"},
        {"cell": [-1, 0], "reason": "blocked"},
        {"cell": [0, -1], "reason": "blocked"},
    ]
    cat, conf, _ = _s4fc.compute_step4_failure_classification(
        stop_reason="exhausted",
        last_error="no_route_exhausted",
        nearest_transport_hops=2,
        near=near,
        goal_cells_count=1,
        reachable_goal_count=0,
        cells={},
        want_role="belt",
        stub_cell=stub,
        hard_extras=frozenset(),
        frontier_stop_reason="exhausted",
    )
    assert cat == _s4fc.Step4FailureCategory.stub_isolated.value
    assert conf == "high"


def test_t3_unknown_insufficient_evidence() -> None:
    stub: Coord = (0, 0)
    near = [
        {"cell": [0, 1], "reason": "ok"},
        {"cell": [1, 0], "reason": "ok"},
        {"cell": [-1, 0], "reason": "ok"},
        {"cell": [0, -1], "reason": "ok"},
    ]
    cat, conf, _ = _s4fc.compute_step4_failure_classification(
        stop_reason="exhausted",
        last_error="no_route_exhausted",
        nearest_transport_hops=2,
        near=near,
        goal_cells_count=0,
        reachable_goal_count=0,
        cells={},
        want_role="belt",
        stub_cell=stub,
        hard_extras=frozenset(),
        frontier_stop_reason="exhausted",
        expanded_nodes=1,
    )
    assert cat == _s4fc.Step4FailureCategory.unknown.value
    assert conf == "low"


def test_t3_mixed_transport_contamination_goal_pipe_for_belt_route() -> None:
    stub: Coord = (0, 0)
    g: Coord = (2, 3)
    near = [
        {"cell": [0, 1], "reason": "ok"},
        {"cell": [1, 0], "reason": "ok"},
        {"cell": [-1, 0], "reason": "ok"},
        {"cell": [0, -1], "reason": "ok"},
    ]
    cat, conf, _ = _s4fc.compute_step4_failure_classification(
        stop_reason="exhausted",
        last_error="no_route_exhausted",
        nearest_transport_hops=2,
        near=near,
        goal_cells_count=1,
        reachable_goal_count=0,
        cells={g: {"role": "pipe", "surface": "fluid"}},
        want_role="belt",
        stub_cell=stub,
        hard_extras=frozenset(),
        goal_cells=frozenset({g}),
        frontier_stop_reason="exhausted",
    )
    assert cat == _s4fc.Step4FailureCategory.mixed_transport_contamination.value
    assert conf == "medium"
