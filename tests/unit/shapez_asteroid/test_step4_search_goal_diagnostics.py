"""STEP4 search goal ordering + Manhattan / frontier diagnostics (wide_search audit)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role as wr,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_search_diagnostics as _s4sd,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_dijkstra import (
    dijkstra_route_step4,
)


def test_merge_goal_union_meta_trunk_before_margin_lex() -> None:
    stub: Coord = (0, 0)
    raw = {(10, 0), (2, 0)}
    trunk = frozenset({(1, 0), (3, 0)})
    margin = {(10, 0), (99, 99)}
    union, meta = _s4sd.merge_goal_union_meta(
        stub, raw_goal=set(raw), trunk_cells=trunk, margin_cells=margin
    )
    assert union == frozenset(raw | trunk)
    assert meta["applied"] is True
    assert meta["mode"] == _s4sd.STEP4_SEARCH_GOAL_ORDERING_MODE
    head = list(meta["priority_head"])
    assert head[0] == [1, 0]
    assert head[1] == [3, 0]
    assert head[2] == [10, 0]
    assert head[3] == [2, 0]


def test_goal_distance_bucket_and_nearest_first() -> None:
    stub: Coord = (0, 0)
    goals = frozenset({(2, 0), (0, 3), (10, 0)})
    b = _s4sd.goal_count_by_distance_bucket(stub, goals)
    assert b["0-4"] == 2
    assert b["9-12"] == 1
    nd, fg = _s4sd.nearest_goal_manhattan_and_first(stub, goals)
    assert nd == 2.0
    assert fg == [2, 0]


def test_fill_goal_geometry_empty_goals() -> None:
    stats: dict = {}
    _s4sd.fill_goal_geometry_search_stats((1, 1), frozenset(), stats)
    assert stats.get("nearest_goal_distance_estimate") is None
    assert stats.get("first_goal_candidate") is None
    assert stats.get("goal_count_by_distance_bucket") == {}


def test_dijkstra_search_stats_frontier_and_geometry() -> None:
    """Minimal map: stub reaches a near goal cell."""

    want = wr("shape_belt")
    cells = {
        (1, 0): {"role": "belt", "surface": "shape"},
        (2, 0): {"role": "belt", "surface": "shape"},
    }
    mineable: frozenset[Coord] = frozenset()
    asteroid: frozenset[Coord] = frozenset()
    goals = frozenset({(2, 0)})
    stats: dict = {}
    path = dijkstra_route_step4(
        (1, 0),
        want_role=want,
        cells=cells,
        blocked=frozenset(),
        mineable=mineable,
        asteroid=asteroid,
        is_external=lambda c: c == (3, 0),
        trunk=frozenset({(2, 0)}),
        goal_cells=goals,
        search_stats=stats,
    )
    assert path is not None
    assert stats["stop_reason"] == "success"
    assert stats["frontier_stop_reason"] == "success"
    assert stats["nearest_goal_distance_estimate"] == 1.0
    assert stats["first_goal_candidate"] == [2, 0]
    assert stats["max_frontier_size"] >= 1
    assert "0-4" in stats["goal_count_by_distance_bucket"]


def test_dijkstra_wide_search_exhausted_guess_budget() -> None:
    """Tiny pop cap forces budget stop; geometry keys still populated."""

    want = wr("shape_belt")
    cells = {(1, 0): {"role": "belt", "surface": "shape"}}
    mineable: frozenset[Coord] = frozenset()
    asteroid: frozenset[Coord] = frozenset()
    goals = frozenset({(50, 50), (51, 51)})
    stats: dict = {}
    path = dijkstra_route_step4(
        (1, 0),
        want_role=want,
        cells=cells,
        blocked=frozenset(),
        mineable=mineable,
        asteroid=asteroid,
        is_external=lambda _: False,
        trunk=frozenset(),
        goal_cells=goals,
        search_stats=stats,
        max_heap_pops=1,
    )
    assert path is None
    assert stats["stop_reason"] == "budget"
    assert stats["frontier_stop_reason"] == "budget"
    assert stats["nearest_goal_distance_estimate"] == 99.0
    assert stats["max_frontier_size"] >= 1
