"""STEP4 ``step4_route_failure_detail`` + Dijkstra ``search_stats``."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_dijkstra as dij_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_detail as s4fd_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_dijkstra import (
    DIJKSTRA_REACHABLE_GOAL_COUNT_KEY,
    DIJKSTRA_REACHABLE_MARGIN_GOAL_COUNT_KEY,
    DIJKSTRA_REACHABLE_TRUNK_GOAL_COUNT_KEY,
    dijkstra_route_step4,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_models import (
    Step4RouteAttemptResult,
)


def _never_external(_c: Coord) -> bool:
    return False


def _assert_top_level_canonical_contract(detail: dict[str, Any]) -> None:
    """T1: every ``step4_route_failure_detail`` exposes flat canonical keys."""

    missing = [
        k for k in s4fd_mod.STEP4_ROUTE_FAILURE_DETAIL_TOP_LEVEL_CANONICAL_KEYS if k not in detail
    ]
    assert not missing, f"missing canonical keys: {missing}"


def _legacy_extra_keys() -> frozenset[str]:
    return frozenset(
        {
            "extractor_cell",
            "nearest_existing_transport_distance",
            "nearest_existing_transport_cell",
            "routing_failure_detail",
            "step4_replay_overlay",
        }
    )


def test_dijkstra_search_stats_exhausted_fully_blocked_stub() -> None:
    stub: Coord = (2, 2)
    cells = {
        stub: {"x": 2, "y": 2, "role": "belt", "surface": "shape"},
    }
    blocked = frozenset({(2, 3), (3, 2), (1, 2), (2, 1)})
    mineable: frozenset[Coord] = frozenset()
    asteroid: frozenset[Coord] = frozenset()
    trunk: frozenset[Coord] = frozenset()
    stats: dict[str, Any] = {}
    path = dijkstra_route_step4(
        stub,
        want_role="belt",
        cells=cells,
        blocked=blocked,
        mineable=mineable,
        asteroid=asteroid,
        is_external=_never_external,
        trunk=trunk,
        goal_cells=frozenset({(99, 99)}),
        cheap_reuse_cells=None,
        search_stats=stats,
    )
    assert path is None
    assert stats["stop_reason"] == "exhausted"
    assert stats["expanded_nodes"] == 1
    assert stats["heap_pops"] >= 1


def test_dijkstra_search_stats_budget() -> None:
    stub: Coord = (2, 2)
    cells = {
        stub: {"x": 2, "y": 2, "role": "belt", "surface": "shape"},
    }
    blocked = frozenset({(2, 3), (3, 2), (1, 2)})  # leave (2,1) open
    mineable = frozenset({(2, 1)})
    asteroid: frozenset[Coord] = frozenset()
    trunk: frozenset[Coord] = frozenset()
    stats: dict[str, Any] = {}
    with patch.object(dij_mod, "_MAX_STEP4_DIJKSTRA_POPS", 1):
        path = dijkstra_route_step4(
            stub,
            want_role="belt",
            cells=cells,
            blocked=blocked,
            mineable=mineable,
            asteroid=asteroid,
            is_external=_never_external,
            trunk=trunk,
            goal_cells=frozenset({(99, 99)}),
            cheap_reuse_cells=None,
            search_stats=stats,
        )
    assert path is None
    assert stats["stop_reason"] == "budget"
    assert "expanded_nodes" in stats


def test_build_step4_route_failure_detail_shape_matches_contract() -> None:
    stub: Coord = (2, 2)
    ext: Coord = (2, 3)
    cells = {
        stub: {"x": 2, "y": 2, "role": "belt", "surface": "shape"},
        ext: {"x": 2, "y": 3, "role": "occupied", "layout_kind": "miner", "surface": "shape"},
    }
    blocked = frozenset({(3, 2), (1, 2), (2, 1)})
    hard = frozenset({(3, 2)})
    detail = s4fd_mod.build_step4_route_failure_detail(
        placement_id="p-test",
        extractor_cell=ext,
        stub_cell=stub,
        transport_kind="shape_belt",
        want_role="belt",
        blocked=blocked,
        hard_extras=hard,
        trunk_cells=frozenset(),
        goal_cells=frozenset({(10, 10)}),
        margin_cells={(10, 10)},
        transport_now=set(),
        cells=cells,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=_never_external,
        cheap_reuse_cells=None,
        search_stats={"stop_reason": "exhausted", "expanded_nodes": 3, "heap_pops": 4},
    )
    assert detail["last_error"] == "no_route_exhausted"
    assert detail["search_mode"] == "goal_cells_union_legacy"
    assert detail["fallback_reason"] is None
    _assert_top_level_canonical_contract(detail)
    assert _legacy_extra_keys() <= frozenset(detail)
    assert detail["search_budget_exhausted"] is False
    assert detail["extractor_id"] == "p-test"
    assert detail["placement_commit_state"] is None
    assert detail["failure_detail_phase"] is None
    assert detail["attempt_index"] == 0
    assert detail["rollback_reason"] is None
    assert detail["rejected_reason"] is None
    assert detail["frontier_stop_reason"] is None
    keys = list(s4fd_mod.ROUTING_FAILURE_DETAIL_KEYS)
    assert list(detail["routing_failure_detail"].keys()) == keys
    rfd = detail["routing_failure_detail"]
    assert rfd["placement_id"] == "p-test"
    assert rfd["transport_kind"] == "shape_belt"
    assert rfd["search_budget_exhausted"] is False
    assert rfd["replacement_search_exhausted"] is None
    assert rfd["quarantined"] is False
    assert rfd["rolled_back"] is False
    assert isinstance(detail["blocked_reason_near_stub"], list)
    assert len(detail["blocked_reason_near_stub"]) == 4
    assert rfd["trunk_seed_candidate_count"] == 0
    assert rfd["candidate_expanded_nodes"] == 3
    assert rfd["step4_failure_category"] == detail["step4_failure_category"]
    assert isinstance(rfd["step4_failure_classification"], dict)
    assert rfd["step4_failure_classification"]["category"] == rfd["step4_failure_category"]
    assert rfd["step4_failure_classification"]["confidence"] in ("high", "medium", "low")
    assert "evidence" in rfd["step4_failure_classification"]
    assert rfd["step4_failure_classification"] == detail["step4_failure_classification"]
    ro = detail.get("step4_replay_overlay")
    assert isinstance(ro, dict)
    assert ro["failed_stub_cells"] == [[2, 2]]
    assert ro["route_goal_cells_sample"] == [[10, 10]]
    js = json.dumps(detail["routing_failure_detail"], sort_keys=True)
    js2 = json.dumps(detail["routing_failure_detail"], sort_keys=True)
    assert js == js2


def test_route_failure_detail_classification_same_with_route_attempt() -> None:
    stub: Coord = (2, 2)
    ext: Coord = (2, 3)
    cells = {
        stub: {"x": 2, "y": 2, "role": "belt", "surface": "shape"},
        ext: {"x": 2, "y": 3, "role": "occupied", "layout_kind": "miner", "surface": "shape"},
    }
    blocked = frozenset({(3, 2), (1, 2), (2, 1)})
    hard = frozenset({(3, 2)})
    stats: dict[str, Any] = {"stop_reason": "exhausted", "expanded_nodes": 3, "heap_pops": 4}
    common: dict[str, Any] = {
        "placement_id": "p-test",
        "extractor_cell": ext,
        "stub_cell": stub,
        "transport_kind": "shape_belt",
        "want_role": "belt",
        "blocked": blocked,
        "hard_extras": hard,
        "trunk_cells": frozenset(),
        "goal_cells": frozenset({(10, 10)}),
        "margin_cells": {(10, 10)},
        "transport_now": set(),
        "cells": cells,
        "mineable": frozenset(),
        "asteroid": frozenset(),
        "is_external": _never_external,
        "cheap_reuse_cells": None,
        "search_stats": stats,
    }
    detail_legacy = s4fd_mod.build_step4_route_failure_detail(**common)
    attempt = Step4RouteAttemptResult.capture(None, dict(stats))
    detail_attempt = s4fd_mod.build_step4_route_failure_detail(**common, route_attempt=attempt)
    assert detail_legacy["step4_failure_category"] == detail_attempt["step4_failure_category"]
    leg_cls = detail_legacy["step4_failure_classification"]
    att_cls = detail_attempt["step4_failure_classification"]
    assert leg_cls == att_cls
    assert detail_legacy["routing_failure_detail"]["step4_failure_category"] == (
        detail_attempt["routing_failure_detail"]["step4_failure_category"]
    )


def test_routing_failure_detail_lifecycle_and_rolled_back_patch() -> None:
    stub: Coord = (2, 2)
    cells = {stub: {"x": 2, "y": 2, "role": "belt", "surface": "shape"}}
    detail = s4fd_mod.build_step4_route_failure_detail(
        placement_id="p2-000001",
        extractor_cell=(2, 3),
        stub_cell=stub,
        transport_kind="shape_belt",
        want_role="belt",
        blocked=frozenset(),
        hard_extras=frozenset(),
        trunk_cells=frozenset(),
        goal_cells=frozenset({(5, 5)}),
        margin_cells={(5, 5)},
        transport_now=set(),
        cells=cells,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=_never_external,
        cheap_reuse_cells=None,
        search_stats={"stop_reason": "exhausted", "expanded_nodes": 1},
        trunk_seed_candidate_count=7,
    )
    rfd = detail["routing_failure_detail"]
    assert rfd["trunk_seed_candidate_count"] == 7
    s4fd_mod.apply_routing_failure_detail_lifecycle(
        detail,
        replacement_search_exhausted=True,
        quarantined=True,
        placement_commit_state="quarantined_unrouted",
    )
    assert rfd["replacement_search_exhausted"] is True
    assert rfd["quarantined"] is True
    assert rfd["placement_commit_state"] == "quarantined_unrouted"
    assert detail["quarantined"] is True
    assert detail["replacement_search_exhausted"] is True
    assert detail["placement_commit_state"] == "quarantined_unrouted"
    fd = {"step4_route_failure_detail": detail, "routing_failure_detail": rfd}
    s4fd_mod.patch_failure_row_routing_failure_detail_rolled_back(fd)
    assert rfd["rolled_back"] is True
    assert detail["rolled_back"] is True
    s4fd_mod.sync_routing_failure_detail_placement_commit_state(fd, "rolled_back")
    fd["rollback_reason"] = "no_route"
    fd["rejected_reason"] = "recovery_exhausted"
    s4fd_mod.stamp_final_step4_route_failure_detail_trace_from_fd(fd, attempt_index=2)
    assert detail["failure_detail_phase"] == "final"
    assert detail["attempt_index"] == 2
    assert detail["rollback_reason"] == "no_route"
    assert detail["rejected_reason"] == "recovery_exhausted"
    assert "commit_reason" not in detail


def test_build_step4_route_failure_detail_placement_commit_state_at_attempt() -> None:
    stub: Coord = (2, 2)
    cells = {stub: {"x": 2, "y": 2, "role": "belt", "surface": "shape"}}
    detail = s4fd_mod.build_step4_route_failure_detail(
        placement_id="p2-000099",
        extractor_cell=(2, 3),
        stub_cell=stub,
        transport_kind="shape_belt",
        want_role="belt",
        blocked=frozenset(),
        hard_extras=frozenset(),
        trunk_cells=frozenset(),
        goal_cells=frozenset({(5, 5)}),
        margin_cells={(5, 5)},
        transport_now=set(),
        cells=cells,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=_never_external,
        cheap_reuse_cells=None,
        search_stats={"stop_reason": "exhausted", "expanded_nodes": 1},
        placement_commit_state_at_route_attempt="provisional_placed",
    )
    assert detail["placement_commit_state"] == "provisional_placed"
    assert detail["routing_failure_detail"]["placement_commit_state"] == "provisional_placed"


def test_build_step4_route_failure_detail_no_stats_last_error_generic() -> None:
    stub: Coord = (2, 2)
    cells = {stub: {"x": 2, "y": 2, "role": "belt", "surface": "shape"}}
    detail = s4fd_mod.build_step4_route_failure_detail(
        placement_id=None,
        extractor_cell=(2, 3),
        stub_cell=stub,
        transport_kind="shape_belt",
        want_role="belt",
        blocked=frozenset(),
        hard_extras=frozenset(),
        trunk_cells=frozenset(),
        goal_cells=frozenset(),
        margin_cells=set(),
        transport_now=set(),
        cells=cells,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=_never_external,
        cheap_reuse_cells=None,
        search_stats={},
    )
    assert detail["last_error"] == "no_route"
    _assert_top_level_canonical_contract(detail)
    assert detail["expanded_nodes"] == 0
    assert detail["candidate_expanded_nodes"] == 0
    assert detail["extractor_id"] is None
    assert detail["frontier_stop_reason"] is None
    rfd = detail["routing_failure_detail"]
    assert rfd["route_goal_set_size"] == 0
    assert rfd["reachable_goal_count"] == 0
    assert rfd["candidate_expanded_nodes"] is None
    assert rfd["extractor_id"] is None


def test_search_budget_exhausted_true_only_for_budget_stop() -> None:
    stub: Coord = (2, 2)
    cells = {stub: {"x": 2, "y": 2, "role": "belt", "surface": "shape"}}
    detail = s4fd_mod.build_step4_route_failure_detail(
        placement_id="p-budget",
        extractor_cell=(2, 3),
        stub_cell=stub,
        transport_kind="shape_belt",
        want_role="belt",
        blocked=frozenset(),
        hard_extras=frozenset(),
        trunk_cells=frozenset(),
        goal_cells=frozenset({(9, 9)}),
        margin_cells={(9, 9)},
        transport_now=set(),
        cells=cells,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=_never_external,
        cheap_reuse_cells=None,
        search_stats={"stop_reason": "budget", "expanded_nodes": 2},
    )
    assert detail["last_error"] == "no_route_budget"
    assert detail["search_budget_exhausted"] is True
    assert detail["routing_failure_detail"]["search_budget_exhausted"] is True
    _assert_top_level_canonical_contract(detail)


def test_sync_placement_commit_state_mirrors_top_level() -> None:
    stub: Coord = (2, 2)
    cells = {stub: {"x": 2, "y": 2, "role": "belt", "surface": "shape"}}
    detail = s4fd_mod.build_step4_route_failure_detail(
        placement_id="p-sync",
        extractor_cell=(2, 3),
        stub_cell=stub,
        transport_kind="shape_belt",
        want_role="belt",
        blocked=frozenset(),
        hard_extras=frozenset(),
        trunk_cells=frozenset(),
        goal_cells=frozenset({(5, 5)}),
        margin_cells={(5, 5)},
        transport_now=set(),
        cells=cells,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=_never_external,
        cheap_reuse_cells=None,
        search_stats={"stop_reason": "exhausted", "expanded_nodes": 1},
    )
    fd = {
        "step4_route_failure_detail": detail,
        "routing_failure_detail": detail["routing_failure_detail"],
    }
    s4fd_mod.sync_routing_failure_detail_placement_commit_state(fd, "rolled_back")
    assert detail["placement_commit_state"] == "rolled_back"
    assert detail["routing_failure_detail"]["placement_commit_state"] == "rolled_back"


def test_t2_exhausted_nonempty_goals_frontier_reachable_zero() -> None:
    """T2: exhausted search with goals outside cage → Dijkstra never pops a goal cell."""

    stub: Coord = (2, 2)
    cells = {
        stub: {"x": 2, "y": 2, "role": "belt", "surface": "shape"},
    }
    blocked = frozenset({(2, 3), (3, 2), (1, 2), (2, 1)})
    goals = frozenset({(99, 99)})
    margin = {(99, 99)}
    stats: dict[str, Any] = {}
    path = dijkstra_route_step4(
        stub,
        want_role="belt",
        cells=cells,
        blocked=blocked,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=lambda c: c in margin,
        trunk=frozenset(),
        goal_cells=goals,
        margin_cells=frozenset(margin),
        search_stats=stats,
    )
    assert path is None
    assert stats["stop_reason"] == "exhausted"
    assert stats["frontier_stop_reason"] == "exhausted"
    assert stats[DIJKSTRA_REACHABLE_GOAL_COUNT_KEY] == 0
    assert stats[DIJKSTRA_REACHABLE_TRUNK_GOAL_COUNT_KEY] == 0
    assert stats[DIJKSTRA_REACHABLE_MARGIN_GOAL_COUNT_KEY] == 0

    detail = s4fd_mod.build_step4_route_failure_detail(
        placement_id="p-t2",
        extractor_cell=(2, 3),
        stub_cell=stub,
        transport_kind="shape_belt",
        want_role="belt",
        blocked=blocked,
        hard_extras=frozenset(),
        trunk_cells=frozenset(),
        goal_cells=goals,
        margin_cells=margin,
        transport_now=set(),
        cells=cells,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=lambda c: c in margin,
        cheap_reuse_cells=None,
        search_stats=stats,
    )
    assert detail["route_goal_set_size"] == 1
    assert detail["reachable_goal_count"] == 0
    assert detail["reachable_existing_trunk_count"] == 0
    assert detail["reachable_exterior_margin_count"] == 0
    assert detail["search_budget_exhausted"] is False
    _assert_top_level_canonical_contract(detail)


def test_t2_budget_does_not_imply_topology_unreachable_proof() -> None:
    """T2: budget stop stamps reachable counts from partial frontier; budget flag is separate."""

    stub: Coord = (1, 0)
    cells = {stub: {"x": 1, "y": 0, "role": "belt", "surface": "shape"}}
    goals = frozenset({(50, 50), (51, 51)})
    stats: dict[str, Any] = {}
    path = dijkstra_route_step4(
        stub,
        want_role="belt",
        cells=cells,
        blocked=frozenset(),
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=lambda _: False,
        trunk=frozenset(),
        goal_cells=goals,
        margin_cells=frozenset(goals),
        search_stats=stats,
        max_heap_pops=1,
    )
    assert path is None
    assert stats["stop_reason"] == "budget"
    assert stats["frontier_stop_reason"] == "budget"
    assert DIJKSTRA_REACHABLE_GOAL_COUNT_KEY in stats
    detail = s4fd_mod.build_step4_route_failure_detail(
        placement_id="p-t2b",
        extractor_cell=(0, 0),
        stub_cell=stub,
        transport_kind="shape_belt",
        want_role="belt",
        blocked=frozenset(),
        hard_extras=frozenset(),
        trunk_cells=frozenset(),
        goal_cells=goals,
        margin_cells=set(goals),
        transport_now=set(),
        cells=cells,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=lambda _: False,
        cheap_reuse_cells=None,
        search_stats=stats,
    )
    assert detail["search_budget_exhausted"] is True
    assert detail["reachable_goal_count"] == stats[DIJKSTRA_REACHABLE_GOAL_COUNT_KEY]
    _assert_top_level_canonical_contract(detail)


def test_t2_success_counts_trunk_goal_before_margin_goal() -> None:
    """T2: first popped goal is on trunk → trunk reachable 1, margin reachable 0."""

    stub: Coord = (1, 0)
    cells = {
        stub: {"x": 1, "y": 0, "role": "belt", "surface": "shape"},
        (2, 0): {"x": 2, "y": 0, "role": "belt", "surface": "shape"},
        (3, 0): {"x": 3, "y": 0, "role": "belt", "surface": "shape"},
        (4, 0): {"x": 4, "y": 0, "role": "belt", "surface": "shape"},
        (5, 0): {"x": 5, "y": 0, "role": "belt", "surface": "shape"},
    }
    mineable = frozenset(cells)
    goals = frozenset({(2, 0), (5, 0)})
    trunk = frozenset({(2, 0)})
    margin = frozenset({(5, 0)})
    stats: dict[str, Any] = {}
    path = dijkstra_route_step4(
        stub,
        want_role="belt",
        cells=cells,
        blocked=frozenset(),
        mineable=mineable,
        asteroid=frozenset(),
        is_external=lambda c: c == (5, 0),
        trunk=trunk,
        goal_cells=goals,
        margin_cells=margin,
        search_stats=stats,
    )
    assert path is not None
    assert stats[DIJKSTRA_REACHABLE_GOAL_COUNT_KEY] == 1
    assert stats[DIJKSTRA_REACHABLE_TRUNK_GOAL_COUNT_KEY] == 1
    assert stats[DIJKSTRA_REACHABLE_MARGIN_GOAL_COUNT_KEY] == 0


def test_t2_success_counts_margin_goal_when_reached_first() -> None:
    """T2: margin goal one step from stub; trunk goal farther → margin reachable 1, trunk 0."""

    stub: Coord = (0, 0)
    cells = {
        stub: {"x": 0, "y": 0, "role": "belt", "surface": "shape"},
        (1, 0): {"x": 1, "y": 0, "role": "belt", "surface": "shape"},
        (0, 1): {"x": 0, "y": 1, "role": "belt", "surface": "shape"},
        (0, 2): {"x": 0, "y": 2, "role": "belt", "surface": "shape"},
        (0, 3): {"x": 0, "y": 3, "role": "belt", "surface": "shape"},
    }
    mineable = frozenset(cells)
    goals = frozenset({(1, 0), (0, 3)})
    trunk = frozenset({(0, 3)})
    margin = frozenset({(1, 0)})
    stats: dict[str, Any] = {}
    path = dijkstra_route_step4(
        stub,
        want_role="belt",
        cells=cells,
        blocked=frozenset(),
        mineable=mineable,
        asteroid=frozenset(),
        is_external=lambda c: c == (1, 0),
        trunk=trunk,
        goal_cells=goals,
        margin_cells=margin,
        search_stats=stats,
    )
    assert path is not None
    assert stats[DIJKSTRA_REACHABLE_GOAL_COUNT_KEY] == 1
    assert stats[DIJKSTRA_REACHABLE_TRUNK_GOAL_COUNT_KEY] == 0
    assert stats[DIJKSTRA_REACHABLE_MARGIN_GOAL_COUNT_KEY] == 1


def test_t2_reachable_fields_present_on_every_failure_detail() -> None:
    stub: Coord = (2, 2)
    cells = {stub: {"x": 2, "y": 2, "role": "belt", "surface": "shape"}}
    detail = s4fd_mod.build_step4_route_failure_detail(
        placement_id="p-fields",
        extractor_cell=(2, 3),
        stub_cell=stub,
        transport_kind="shape_belt",
        want_role="belt",
        blocked=frozenset(),
        hard_extras=frozenset(),
        trunk_cells=frozenset({(5, 5)}),
        goal_cells=frozenset({(5, 5), (6, 6)}),
        margin_cells={(6, 6)},
        transport_now=set(),
        cells=cells,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=_never_external,
        cheap_reuse_cells=None,
        search_stats={"stop_reason": "exhausted", "expanded_nodes": 1},
    )
    for k in (
        "reachable_goal_count",
        "reachable_existing_trunk_count",
        "reachable_exterior_margin_count",
        "route_goal_set_size",
        "active_goal_cells_count",
        "margin_goals_in_active_goal_cells_count",
        "existing_trunk_goal_count",
        "external_goal_count",
        "trunk_seed_candidate_count",
    ):
        assert k in detail
    rfd = detail["routing_failure_detail"]
    for k in (
        "reachable_goal_count",
        "reachable_existing_trunk_count",
        "reachable_exterior_margin_count",
        "route_goal_set_size",
        "active_goal_cells_count",
        "margin_goals_in_active_goal_cells_count",
        "trunk_seed_candidate_count",
    ):
        assert k in rfd
    assert "step4_failure_category" in detail
    assert "step4_failure_classification" in detail
    clf = detail["step4_failure_classification"]
    assert clf["category"] == detail["step4_failure_category"]
    assert clf["confidence"] in ("high", "medium", "low")
    assert "evidence" in clf
