"""Sequence 3 — route feasibility probe."""

from __future__ import annotations

import time

import pytest

from django_apps.shapez_asteroid.optimization.coords import Coord, neighbors4_server
from django_apps.shapez_asteroid.optimization.dto import (
    RouteCellDomain,
    RouteGoal,
    RouteProbeInput,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
)
from django_apps.shapez_asteroid.optimization.enums import (
    EdgeKind,
    RouteClass,
    RouteGoalKind,
    RouteProbeFailureReason,
    TopologyNodeKind,
    TransportKind,
    TransportMask,
)
from django_apps.shapez_asteroid.optimization.route_probe import run_route_probe


def _canon_edge(a: Coord, b: Coord, cost: int = 1) -> TopologyEdge:
    if (a.x, a.y) <= (b.x, b.y):
        return TopologyEdge(a=a, b=b, edge_kind=EdgeKind.CARDINAL, traversal_cost=cost)
    return TopologyEdge(a=b, b=a, edge_kind=EdgeKind.CARDINAL, traversal_cost=cost)


def _cell_domain(
    c: Coord,
    *,
    cost: int = 1,
    hard: bool = False,
    mask: TransportMask = TransportMask.BOTH,
) -> RouteCellDomain:
    return RouteCellDomain(
        coord=c,
        route_class=RouteClass.STANDARD,
        traversal_cost=cost,
        hard_blocked=hard,
        carve_allowed=False,
        transport_mask=mask,
    )


def _line_topology(*coords: Coord) -> TopologyGraph:
    nodes = frozenset(
        TopologyNode(coord=c, node_kind=TopologyNodeKind.EXTERNAL_VOID) for c in coords
    )
    edges: set[TopologyEdge] = set()
    cs = sorted(coords, key=lambda z: (z.x, z.y))
    for i in range(len(cs) - 1):
        edges.add(_canon_edge(cs[i], cs[i + 1]))
    return TopologyGraph(nodes=nodes, edges=frozenset(edges))


def test_route_probe_reaches_prioritized_route_goal() -> None:
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    domain = {c: _cell_domain(c) for c in (c0, c1, c2)}
    g_hi = RouteGoal(c2, RouteGoalKind.EXTERNAL_MARGIN, None, priority=5, existing_trunk=False)
    g_lo = RouteGoal(c2, RouteGoalKind.SOFT_CORRIDOR, None, priority=1, existing_trunk=False)
    topo = _line_topology(c0, c1, c2)
    inp = RouteProbeInput(
        start=c0,
        goals=frozenset({g_hi, g_lo}),
        route_domain=domain,
        topology_graph=topo,
        max_expansions=50,
        transport_kind=TransportKind.SHAPE_BELT,
        goal_priority_weight=10,
    )
    res = run_route_probe(inp)
    assert res.reachable
    assert res.reached_goal is not None
    assert res.reached_goal is g_lo
    assert res.goal_priority == 1


def test_route_probe_respects_topology_graph_adjacency() -> None:
    """Vertical link absent: graph is a horizontal strip only."""

    a, b, c = Coord(0, 0), Coord(1, 0), Coord(0, 1)
    domain = {x: _cell_domain(x) for x in (a, b, c)}
    topo = _line_topology(a, b)
    goal = RouteGoal(b, RouteGoalKind.EXTERNAL_MARGIN, None, priority=0, existing_trunk=False)
    inp = RouteProbeInput(
        start=a,
        goals=frozenset({goal}),
        route_domain=domain,
        topology_graph=topo,
        max_expansions=20,
        transport_kind=TransportKind.SHAPE_BELT,
        goal_priority_weight=1,
    )
    ok = run_route_probe(inp)
    assert ok.reachable

    goal_c = RouteGoal(c, RouteGoalKind.EXTERNAL_MARGIN, None, priority=0, existing_trunk=False)
    bad = run_route_probe(
        RouteProbeInput(
            start=a,
            goals=frozenset({goal_c}),
            route_domain=domain,
            topology_graph=topo,
            max_expansions=20,
            transport_kind=TransportKind.SHAPE_BELT,
            goal_priority_weight=1,
        )
    )
    assert not bad.reachable
    assert bad.failure_reason is RouteProbeFailureReason.EXHAUSTED


def test_route_probe_neighbors4_server_fallback_when_no_edges() -> None:
    c0, c1 = Coord(0, 0), Coord(1, 0)
    domain = {c: _cell_domain(c) for c in (c0, c1)}
    topo = TopologyGraph(nodes=frozenset(), edges=frozenset())
    goal = RouteGoal(c1, RouteGoalKind.EXTERNAL_MARGIN, None, priority=0, existing_trunk=False)
    res = run_route_probe(
        RouteProbeInput(
            start=c0,
            goals=frozenset({goal}),
            route_domain=domain,
            topology_graph=topo,
            max_expansions=10,
            transport_kind=TransportKind.SHAPE_BELT,
            goal_priority_weight=1,
        )
    )
    assert res.reachable
    assert res.path == (c0, c1)
    assert c1 in neighbors4_server(c0)


def test_route_probe_never_crosses_hard_blocked() -> None:
    a, m, b = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    domain = {
        a: _cell_domain(a),
        m: _cell_domain(m, hard=True),
        b: _cell_domain(b),
    }
    topo = TopologyGraph(
        nodes=frozenset(),
        edges=frozenset({_canon_edge(a, m), _canon_edge(m, b)}),
    )
    goal = RouteGoal(b, RouteGoalKind.EXTERNAL_MARGIN, None, priority=0, existing_trunk=False)
    res = run_route_probe(
        RouteProbeInput(
            start=a,
            goals=frozenset({goal}),
            route_domain=domain,
            topology_graph=topo,
            max_expansions=20,
            transport_kind=TransportKind.SHAPE_BELT,
            goal_priority_weight=1,
        )
    )
    assert not res.reachable
    assert res.failure_reason is RouteProbeFailureReason.EXHAUSTED


def test_route_probe_respects_transport_mask_per_cell() -> None:
    a, b = Coord(0, 0), Coord(1, 0)
    domain = {
        a: _cell_domain(a, mask=TransportMask.SHAPE_BELT),
        b: _cell_domain(b, mask=TransportMask.FLUID_PIPE),
    }
    topo = _line_topology(a, b)
    goal = RouteGoal(b, RouteGoalKind.EXTERNAL_MARGIN, None, priority=0, existing_trunk=False)
    res = run_route_probe(
        RouteProbeInput(
            start=a,
            goals=frozenset({goal}),
            route_domain=domain,
            topology_graph=topo,
            max_expansions=10,
            transport_kind=TransportKind.SHAPE_BELT,
            goal_priority_weight=1,
        )
    )
    assert not res.reachable


def test_route_probe_transport_kind_separation_on_goals() -> None:
    a, b = Coord(0, 0), Coord(1, 0)
    domain = {c: _cell_domain(c) for c in (a, b)}
    topo = _line_topology(a, b)
    g_shape = RouteGoal(
        b, RouteGoalKind.EXISTING_TRANSPORT_ATTACHMENT, TransportKind.SHAPE_BELT, 0, False
    )
    g_fluid = RouteGoal(
        b, RouteGoalKind.EXISTING_TRANSPORT_ATTACHMENT, TransportKind.FLUID_PIPE, 0, False
    )
    shape_res = run_route_probe(
        RouteProbeInput(
            start=a,
            goals=frozenset({g_shape, g_fluid}),
            route_domain=domain,
            topology_graph=topo,
            max_expansions=10,
            transport_kind=TransportKind.SHAPE_BELT,
            goal_priority_weight=1,
        )
    )
    assert shape_res.reached_goal is g_shape
    fluid_res = run_route_probe(
        RouteProbeInput(
            start=a,
            goals=frozenset({g_shape, g_fluid}),
            route_domain=domain,
            topology_graph=topo,
            max_expansions=10,
            transport_kind=TransportKind.FLUID_PIPE,
            goal_priority_weight=1,
        )
    )
    assert fluid_res.reached_goal is g_fluid


def test_route_probe_budget_exceeded() -> None:
    coords = [Coord(i, 0) for i in range(10)]
    domain = {c: _cell_domain(c) for c in coords}
    topo = _line_topology(*coords)
    goal = RouteGoal(coords[-1], RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    res = run_route_probe(
        RouteProbeInput(
            start=coords[0],
            goals=frozenset({goal}),
            route_domain=domain,
            topology_graph=topo,
            max_expansions=2,
            transport_kind=TransportKind.SHAPE_BELT,
            goal_priority_weight=1,
        )
    )
    assert not res.reachable
    assert res.failure_reason is RouteProbeFailureReason.BUDGET_EXCEEDED


def test_route_probe_selection_score_prefers_lower_score_over_path_cost() -> None:
    """Lower ``path_cost + w * priority`` wins even if raw path_cost is higher."""

    s, a, b = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    domain = {
        s: _cell_domain(s),
        a: _cell_domain(a, cost=1),
        b: _cell_domain(b, cost=1),
    }
    topo = _line_topology(s, a, b)
    g_far = RouteGoal(b, RouteGoalKind.EXTERNAL_MARGIN, None, priority=0, existing_trunk=False)
    g_near_badprio = RouteGoal(
        a, RouteGoalKind.EXTERNAL_MARGIN, None, priority=10, existing_trunk=False
    )
    res = run_route_probe(
        RouteProbeInput(
            start=s,
            goals=frozenset({g_far, g_near_badprio}),
            route_domain=domain,
            topology_graph=topo,
            max_expansions=50,
            transport_kind=TransportKind.SHAPE_BELT,
            goal_priority_weight=1,
        )
    )
    assert res.reached_goal is g_far


def test_route_probe_expanded_nodes_counts_pops() -> None:
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    domain = {c: _cell_domain(c) for c in (c0, c1, c2)}
    topo = _line_topology(c0, c1, c2)
    goal = RouteGoal(c2, RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    res = run_route_probe(
        RouteProbeInput(
            start=c0,
            goals=frozenset({goal}),
            route_domain=domain,
            topology_graph=topo,
            max_expansions=50,
            transport_kind=TransportKind.SHAPE_BELT,
            goal_priority_weight=1,
        )
    )
    assert res.reachable
    assert res.expanded_nodes >= 1


def test_route_probe_blocked_by_occupied_only_at_start_trap() -> None:
    s = Coord(1, 0)
    e = Coord(2, 0)
    domain = {
        s: _cell_domain(s),
        Coord(0, 0): _cell_domain(Coord(0, 0)),
        e: _cell_domain(e),
    }
    topo = TopologyGraph(nodes=frozenset(), edges=frozenset())
    goal = RouteGoal(e, RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    res = run_route_probe(
        RouteProbeInput(
            start=s,
            goals=frozenset({goal}),
            route_domain=domain,
            topology_graph=topo,
            max_expansions=20,
            transport_kind=TransportKind.SHAPE_BELT,
            goal_priority_weight=1,
        ),
        occupied_cells=frozenset({Coord(0, 0), Coord(2, 0)}),
    )
    assert res.failure_reason is RouteProbeFailureReason.BLOCKED_BY_OCCUPIED


def test_route_probe_invalid_route_domain_start() -> None:
    c0 = Coord(0, 0)
    domain = {c0: _cell_domain(c0)}
    goal = RouteGoal(c0, RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    res = run_route_probe(
        RouteProbeInput(
            start=Coord(5, 5),
            goals=frozenset({goal}),
            route_domain=domain,
            topology_graph=TopologyGraph(nodes=frozenset(), edges=frozenset()),
            max_expansions=5,
            transport_kind=TransportKind.SHAPE_BELT,
            goal_priority_weight=1,
        )
    )
    assert res.failure_reason is RouteProbeFailureReason.INVALID_ROUTE_DOMAIN


def test_route_probe_no_goal_cells() -> None:
    c0, c1 = Coord(0, 0), Coord(1, 0)
    domain = {c: _cell_domain(c) for c in (c0, c1)}
    topo = _line_topology(c0, c1)
    g = RouteGoal(Coord(9, 9), RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    res = run_route_probe(
        RouteProbeInput(
            start=c0,
            goals=frozenset({g}),
            route_domain=domain,
            topology_graph=topo,
            max_expansions=10,
            transport_kind=TransportKind.SHAPE_BELT,
            goal_priority_weight=1,
        )
    )
    assert res.failure_reason is RouteProbeFailureReason.NO_GOAL_CELLS


def test_route_probe_tie_break_lexicographic_goal_coord() -> None:
    s = Coord(0, 0)
    g1 = RouteGoal(Coord(1, 0), RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    g2 = RouteGoal(Coord(0, 1), RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    domain = {
        Coord(0, 0): _cell_domain(Coord(0, 0)),
        Coord(1, 0): _cell_domain(Coord(1, 0)),
        Coord(0, 1): _cell_domain(Coord(0, 1)),
    }
    topo = TopologyGraph(
        nodes=frozenset(),
        edges=frozenset({_canon_edge(s, Coord(1, 0)), _canon_edge(s, Coord(0, 1))}),
    )
    res = run_route_probe(
        RouteProbeInput(
            start=s,
            goals=frozenset({g1, g2}),
            route_domain=domain,
            topology_graph=topo,
            max_expansions=20,
            transport_kind=TransportKind.SHAPE_BELT,
            goal_priority_weight=1,
        )
    )
    assert res.reached_goal is not None
    assert res.reached_goal.coord == Coord(0, 1)


@pytest.mark.parametrize("kind", list(TransportKind))
def test_route_probe_start_blocked_mask(kind: TransportKind) -> None:
    c0 = Coord(0, 0)
    mask = (
        TransportMask.FLUID_PIPE if kind is TransportKind.SHAPE_BELT else TransportMask.SHAPE_BELT
    )
    domain = {c0: _cell_domain(c0, mask=mask)}
    goal = RouteGoal(c0, RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    res = run_route_probe(
        RouteProbeInput(
            start=c0,
            goals=frozenset({goal}),
            route_domain=domain,
            topology_graph=TopologyGraph(nodes=frozenset(), edges=frozenset()),
            max_expansions=5,
            transport_kind=kind,
            goal_priority_weight=1,
        )
    )
    assert res.failure_reason is RouteProbeFailureReason.START_BLOCKED


def test_route_probe_wall_clock_deadline_aborts_during_search() -> None:
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    domain = {c: _cell_domain(c) for c in (c0, c1, c2)}
    goal = RouteGoal(c2, RouteGoalKind.EXTERNAL_MARGIN, None, priority=0, existing_trunk=False)
    topo = _line_topology(c0, c1, c2)
    inp = RouteProbeInput(
        start=c0,
        goals=frozenset({goal}),
        route_domain=domain,
        topology_graph=topo,
        max_expansions=50,
        transport_kind=TransportKind.SHAPE_BELT,
        goal_priority_weight=1,
        wall_clock_deadline_perf=time.perf_counter() - 1.0,
    )
    res = run_route_probe(inp)
    assert not res.reachable
    assert res.failure_reason is RouteProbeFailureReason.WALL_CLOCK_ABORT
