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
    dijkstra_route_step4,
)


def _never_external(_c: Coord) -> bool:
    return False


def _detail_keys() -> frozenset[str]:
    return frozenset(
        {
            "placement_id",
            "extractor_cell",
            "stub_cell",
            "transport_kind",
            "nearest_existing_transport_distance",
            "nearest_existing_transport_cell",
            "existing_trunk_goal_count",
            "external_goal_count",
            "blocked_reason_near_stub",
            "search_mode",
            "expanded_nodes",
            "fallback_reason",
            "last_error",
            "routing_failure_detail",
            "step4_failure_category",
            "step4_failure_classification",
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
    assert _detail_keys() <= frozenset(detail)
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
    assert rfd["step4_failure_classification"] == detail["step4_failure_classification"]
    ro = detail.get("step4_replay_overlay")
    assert isinstance(ro, dict)
    assert ro["failed_stub_cells"] == [[2, 2]]
    assert ro["route_goal_cells_sample"] == [[10, 10]]
    js = json.dumps(detail["routing_failure_detail"], sort_keys=True)
    js2 = json.dumps(detail["routing_failure_detail"], sort_keys=True)
    assert js == js2


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
    fd = {"step4_route_failure_detail": detail, "routing_failure_detail": rfd}
    s4fd_mod.patch_failure_row_routing_failure_detail_rolled_back(fd)
    assert rfd["rolled_back"] is True


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
    rfd = detail["routing_failure_detail"]
    assert rfd["route_goal_set_size"] == 0
    assert rfd["reachable_goal_count"] == 0
    assert rfd["candidate_expanded_nodes"] is None
    assert rfd["extractor_id"] is None
