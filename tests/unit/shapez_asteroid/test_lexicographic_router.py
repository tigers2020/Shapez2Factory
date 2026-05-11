"""Unit tests for P3-E1 lexicographic route search (isolated from solver_service / Pass3)."""

from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    PASS3_INTERIOR_DEPTH_PENALTY_MAX_DEPTH,
    PASS3_INTERIOR_DEPTH_ROUTE_PENALTY_PER_UNIT,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.lexicographic_router import (  # noqa: E501
    RouteSearchResult,
    _step_deltas,
    find_lexicographic_route,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_zone import (
    KIND_COST_MULTIPLIER,
    ROUTE_ZONE_COST,
    RouteZone,
    TransportKind,
    build_asteroid_boundary_depth_by_cell,
    build_route_zone_map,
    transport_kind_from_solver_value,
)


def _asteroid_rect(x0: int, y0: int, x1: int, y1: int) -> frozenset[tuple[int, int]]:
    return frozenset((x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1))


def _bbox(x0: int, y0: int, x1: int, y1: int) -> frozenset[tuple[int, int]]:
    return frozenset((x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1))


def test_prefers_longer_void_path_when_internal_transport_lower() -> None:
    """Void-only eastbound route from the asteroid face avoids interior re-entry."""

    asteroid = _asteroid_rect(0, 0, 6, 6)
    zm = build_route_zone_map(asteroid_cells=asteroid)
    start = (6, 3)
    goal = (12, 3)
    goals = frozenset({goal})
    allowed = _bbox(-1, -1, 14, 7)

    res = find_lexicographic_route(
        start=start,
        goals=goals,
        route_zone_map=zm,
        transport_kind=TransportKind.SHAPE_BELT,
        blocked_cells=frozenset(),
        existing_transport_cells=frozenset(),
        asteroid_cells=asteroid,
        placement_candidate_cells=frozenset(),
        allowed_cells=allowed,
    )
    assert res.found
    assert res.path[0] == start
    assert res.path[-1] == goal
    interior_hops = sum(1 for c in res.path[1:] if zm.get(c) is RouteZone.ASTEROID_INTERIOR_VOID)
    assert interior_hops == 0, "expected perimeter/void only, not interior corridor"


def test_placement_candidate_cells_raise_opportunity_loss_vs_shorter_path() -> None:
    """Marking the straight void corridor raises opportunity; the solver takes a longer detour."""

    asteroid = _asteroid_rect(0, 0, 0, 4)
    zm = build_route_zone_map(asteroid_cells=asteroid)
    start = (0, 2)
    goal = (5, 2)
    goals = frozenset({goal})
    allowed = _bbox(-1, 0, 6, 4)
    straight = frozenset({(1, 2), (2, 2), (3, 2), (4, 2)})

    res_bad = find_lexicographic_route(
        start=start,
        goals=goals,
        route_zone_map=zm,
        transport_kind=TransportKind.SHAPE_BELT,
        blocked_cells=frozenset(),
        existing_transport_cells=frozenset(),
        asteroid_cells=asteroid,
        placement_candidate_cells=straight,
        allowed_cells=allowed,
    )
    res_good = find_lexicographic_route(
        start=start,
        goals=goals,
        route_zone_map=zm,
        transport_kind=TransportKind.SHAPE_BELT,
        blocked_cells=frozenset(),
        existing_transport_cells=frozenset(),
        asteroid_cells=asteroid,
        placement_candidate_cells=frozenset(),
        allowed_cells=allowed,
    )
    assert res_bad.found and res_good.found
    assert len(res_good.path) == 6
    assert not set(res_bad.path) & straight
    assert len(res_bad.path) > len(res_good.path)


def test_deterministic_tie_breaks_equal_priority_paths_by_coord_sequence() -> None:
    """Two equal-length symmetric routes to the same goal: pick lexicographically smaller path."""

    asteroid = _asteroid_rect(0, 0, 2, 2)
    zm = build_route_zone_map(asteroid_cells=asteroid)
    start = (1, 1)
    goal = (1, 4)
    goals = frozenset({goal})
    blocked = frozenset({(0, 2), (2, 2), (0, 3), (2, 3)})
    allowed = _bbox(-1, -1, 3, 5)

    a = find_lexicographic_route(
        start=start,
        goals=goals,
        route_zone_map=zm,
        transport_kind=TransportKind.SHAPE_BELT,
        blocked_cells=blocked,
        existing_transport_cells=frozenset(),
        asteroid_cells=asteroid,
        placement_candidate_cells=frozenset(),
        allowed_cells=allowed,
    )
    b = find_lexicographic_route(
        start=start,
        goals=goals,
        route_zone_map=zm,
        transport_kind=TransportKind.SHAPE_BELT,
        blocked_cells=blocked,
        existing_transport_cells=frozenset(),
        asteroid_cells=asteroid,
        placement_candidate_cells=frozenset(),
        allowed_cells=allowed,
    )
    assert a.found and b.found
    assert a.path == b.path
    assert a.path[0] == start


def test_blocked_cells_not_traversed() -> None:
    asteroid = frozenset({(0, 0)})
    zm = build_route_zone_map(asteroid_cells=asteroid)
    start = (0, 0)
    goal = (2, 0)
    goals = frozenset({goal})
    blocked = frozenset({(1, 0)})

    allowed_strip = _bbox(0, 0, 2, 0)

    res = find_lexicographic_route(
        start=start,
        goals=goals,
        route_zone_map=zm,
        transport_kind=TransportKind.SHAPE_BELT,
        blocked_cells=blocked,
        existing_transport_cells=frozenset(),
        asteroid_cells=asteroid,
        placement_candidate_cells=frozenset(),
        allowed_cells=allowed_strip,
    )
    assert not res.found
    assert res.fallback_reason == "no_route_to_goals"


def test_expanded_node_budget() -> None:
    asteroid = _asteroid_rect(0, 0, 1, 1)
    zm = build_route_zone_map(asteroid_cells=asteroid)
    start = (0, 0)
    goal = (30, 0)
    goals = frozenset({goal})

    allowed = _bbox(0, 0, 30, 1)

    res = find_lexicographic_route(
        start=start,
        goals=goals,
        route_zone_map=zm,
        transport_kind=TransportKind.SHAPE_BELT,
        blocked_cells=frozenset(),
        existing_transport_cells=frozenset(),
        asteroid_cells=asteroid,
        placement_candidate_cells=frozenset(),
        max_expanded_nodes=3,
        allowed_cells=allowed,
    )
    assert isinstance(res, RouteSearchResult)
    assert not res.found
    assert res.fallback_reason == "expanded_node_budget_exceeded"


def test_pipe_and_belt_share_kind_cost_multiplier_canonical() -> None:
    """Canonical v5.9: same kind multiplier; kind-specific tuning is separate from lex base."""

    assert (
        KIND_COST_MULTIPLIER[TransportKind.SHAPE_BELT]
        == KIND_COST_MULTIPLIER[TransportKind.FLUID_PIPE]
    )
    asteroid = frozenset({(0, 0), (1, 0)})
    zm = build_route_zone_map(asteroid_cells=asteroid)
    start = (0, 0)
    goal = (5, 0)
    goals = frozenset({goal})
    kwargs = dict(
        start=start,
        goals=goals,
        route_zone_map=zm,
        blocked_cells=frozenset(),
        existing_transport_cells=frozenset(),
        asteroid_cells=asteroid,
        placement_candidate_cells=frozenset(),
        allowed_cells=_bbox(0, -1, 5, 1),
    )
    belt = find_lexicographic_route(**kwargs, transport_kind=TransportKind.SHAPE_BELT)
    pipe = find_lexicographic_route(**kwargs, transport_kind=TransportKind.FLUID_PIPE)
    assert belt.found and pipe.found
    assert belt.priority is not None and pipe.priority is not None
    assert pipe.priority[2] == belt.priority[2]


def test_canonical_route_zone_costs_four_zone_map() -> None:
    assert ROUTE_ZONE_COST[RouteZone.EXTERIOR_VOID] == 1
    assert ROUTE_ZONE_COST[RouteZone.ASTEROID_PERIMETER] == 5
    assert ROUTE_ZONE_COST[RouteZone.ASTEROID_INTERIOR_VOID] == 50
    assert ROUTE_ZONE_COST[RouteZone.FILLABLE_INTERIOR] == 150


def test_transport_kind_from_solver_value_roundtrip() -> None:
    assert transport_kind_from_solver_value("shape_belt") is TransportKind.SHAPE_BELT
    assert transport_kind_from_solver_value("fluid_pipe") is TransportKind.FLUID_PIPE
    assert TransportKind.SHAPE_BELT.value == "shape_belt"


def test_transport_kind_from_solver_value_unknown() -> None:
    with pytest.raises(ValueError, match="unknown transport_kind"):
        transport_kind_from_solver_value("belt")


def test_step_deltas_interior_depth_adds_route_cost_only_on_interior_void() -> None:
    """Interior void + depth map increases lex axis 2; exterior cells ignore depth."""

    zm = {(2, 2): RouteZone.ASTEROID_INTERIOR_VOID}
    depth = {(2, 2): 4}
    _, _, dr_int, _, _, _ = _step_deltas(
        prev=None,
        cur=(1, 2),
        nxt=(2, 2),
        route_zone_map=zm,
        transport_kind=TransportKind.SHAPE_BELT,
        existing_transport_cells=set(),
        placement_candidate_cells=set(),
        congestion_step=0,
        interior_depth_by_cell=depth,
    )
    cap = min(4, PASS3_INTERIOR_DEPTH_PENALTY_MAX_DEPTH)
    assert dr_int == ROUTE_ZONE_COST[RouteZone.ASTEROID_INTERIOR_VOID] + (
        PASS3_INTERIOR_DEPTH_ROUTE_PENALTY_PER_UNIT * cap
    )

    _, _, dr_ext, _, _, _ = _step_deltas(
        prev=None,
        cur=(1, 2),
        nxt=(9, 2),
        route_zone_map=zm,
        transport_kind=TransportKind.SHAPE_BELT,
        existing_transport_cells=set(),
        placement_candidate_cells=set(),
        congestion_step=0,
        interior_depth_by_cell={(9, 2): 99},
    )
    assert dr_ext == ROUTE_ZONE_COST[RouteZone.EXTERIOR_VOID]


def test_find_lexicographic_route_avoids_interior_spine_asteroid_only_allowed() -> None:
    """With search confined to the asteroid, depth penalty discourages the central column."""

    ast = frozenset((x, y) for x in range(1, 6) for y in range(1, 6))
    zm = build_route_zone_map(asteroid_cells=ast, mineable_cells=frozenset())
    depth = build_asteroid_boundary_depth_by_cell(asteroid_cells=ast)
    start = (2, 1)
    goal = (2, 5)
    goals = frozenset({goal})

    res = find_lexicographic_route(
        start=start,
        goals=goals,
        route_zone_map=zm,
        transport_kind=TransportKind.SHAPE_BELT,
        blocked_cells=frozenset(),
        existing_transport_cells=frozenset(),
        asteroid_cells=set(ast),
        placement_candidate_cells=frozenset(),
        allowed_cells=set(ast),
        interior_depth_by_cell=depth,
    )
    assert res.found
    assert (2, 3) not in res.path, "expected to avoid deep interior spine column"
    assert all(c in ast for c in res.path)


def test_edge_congestion_weights_accumulate_in_lex_priority() -> None:
    """Lex tuple index 3 (congestion) sums ``edge_congestion_weights`` per canonical edge step."""

    zm: dict[tuple[int, int], RouteZone] = {}
    allowed = frozenset({(1, 0), (2, 0), (3, 0)})
    res = find_lexicographic_route(
        start=(1, 0),
        goals=frozenset({(3, 0)}),
        route_zone_map=zm,
        transport_kind=TransportKind.SHAPE_BELT,
        blocked_cells=frozenset(),
        existing_transport_cells=frozenset(),
        asteroid_cells=frozenset(),
        placement_candidate_cells=frozenset(),
        allowed_cells=allowed,
        edge_congestion_weights={"1,0--2,0": 4, "2,0--3,0": 1},
    )
    assert res.found
    assert res.priority is not None
    assert res.priority[3] == 5


def test_merge_cell_incoming_direction_affects_continuation_turns() -> None:
    """Two equal-length corridors to a merge; prefer heading into the tail with fewer turns.

    Coordinates use x>=1 so :func:`neighbors4` allows north/south (column x=0 forbids NS moves).
    """

    zm: dict[tuple[int, int], RouteZone] = {}
    allowed = frozenset(
        {
            (1, 0),
            (2, 0),
            (3, 0),
            (3, 1),
            (3, 2),
            (1, 1),
            (1, 2),
            (2, 2),
            (4, 2),
            (5, 2),
        }
    )
    res = find_lexicographic_route(
        start=(1, 0),
        goals=frozenset({(5, 2)}),
        route_zone_map=zm,
        transport_kind=TransportKind.SHAPE_BELT,
        blocked_cells=frozenset(),
        existing_transport_cells=frozenset(),
        asteroid_cells=frozenset(),
        placement_candidate_cells=frozenset(),
        allowed_cells=allowed,
    )
    assert res.found
    assert res.path == (
        (1, 0),
        (1, 1),
        (1, 2),
        (2, 2),
        (3, 2),
        (4, 2),
        (5, 2),
    )
