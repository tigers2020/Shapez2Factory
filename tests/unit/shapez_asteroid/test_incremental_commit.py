"""Sequence 6 — incremental route commit."""

from __future__ import annotations

import json
from unittest.mock import patch

from django_apps.shapez_asteroid.optimization.coords import BBox, Coord
from django_apps.shapez_asteroid.optimization.dto import (
    BundleCandidate,
    Gene,
    Genome,
    OptimizationInput,
    RecoveryBudget,
    RouteCellDomain,
    RouteGoal,
    RouteProbeResult,
    RouteReservation,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CardinalDirection,
    CommitConflictReason,
    EdgeKind,
    PlacementCommitState,
    ReservationState,
    RouteClass,
    RouteGoalKind,
    RouteProbeFailureReason,
    TopologyNodeKind,
    TransportKind,
    TransportMask,
)
from django_apps.shapez_asteroid.optimization.incremental_commit import (
    _path_conflict_reason,
    commit_best_genome,
    genome_commit_candidates,
)
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)
from django_apps.shapez_asteroid.optimization.route_probe import (
    run_route_probe as real_run_route_probe,
)


def _canon_edge(a: Coord, b: Coord, cost: int = 1) -> TopologyEdge:
    if (a.x, a.y) <= (b.x, b.y):
        return TopologyEdge(a=a, b=b, edge_kind=EdgeKind.CARDINAL, traversal_cost=cost)
    return TopologyEdge(a=b, b=a, edge_kind=EdgeKind.CARDINAL, traversal_cost=cost)


def _strip_input() -> tuple[OptimizationInput, RouteGoal]:
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    coords = (c0, c1, c2)
    ac = frozenset(coords)
    rim = frozenset({c0, c2})
    mineable = ac
    interior = frozenset({c1})
    ext_void: frozenset[Coord] = frozenset()
    goal = RouteGoal(c2, RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    bbox = BBox(0, 2, 0, 0)
    nodes = frozenset(
        TopologyNode(coord=c, node_kind=TopologyNodeKind.EXTERNAL_VOID) for c in coords
    )
    edges = frozenset({_canon_edge(c0, c1), _canon_edge(c1, c2)})
    topo = TopologyGraph(nodes=nodes, edges=edges)
    inp = OptimizationInput(
        asteroid_cells=ac,
        mineable_cells=mineable,
        rim_cells=rim,
        interior_cells=interior,
        external_void_cells=ext_void,
        route_goals=frozenset({goal}),
        existing_transport_cells=frozenset(),
        existing_trunk_cells=frozenset(),
        protected_corridor_cells=frozenset(),
        blocked_cells=frozenset(),
        topology_graph=topo,
        bbox=bbox,
    )
    return inp, goal


def _ok_probe(path: tuple[Coord, ...], goal: RouteGoal) -> RouteProbeResult:
    return RouteProbeResult(
        reachable=True,
        path=path,
        cost=sum(1 for _ in path),
        expanded_nodes=len(path),
        reached_goal=goal,
        goal_priority=goal.priority,
        failure_reason=None,
    )


def _bundle(
    cid: str,
    *,
    occupied: frozenset[Coord],
    output_stub: Coord,
    transport_kind: TransportKind,
    probe_path: tuple[Coord, ...],
    goal: RouteGoal,
) -> BundleCandidate:
    extractor = min(occupied, key=lambda z: (z.x, z.y))
    extensions = tuple(sorted(occupied - {extractor}, key=lambda z: (z.x, z.y)))
    return BundleCandidate(
        candidate_id=cid,
        pattern_id="p",
        topology_signature="sig",
        extractor=extractor,
        extensions=extensions,
        occupied_cells=occupied,
        output_stub=output_stub,
        output_dir=CardinalDirection.EAST,
        transport_kind=transport_kind,
        base_throughput=1,
        base_score=1.0,
        route_probe_result=_ok_probe(probe_path, goal),
    )


def test_incremental_commit_confirms_connected_candidate() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        _bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    assert res.confirmed_candidate_count == 1
    assert res.rolled_back_candidate_count == 0
    assert len(res.route_reservations) == 1
    assert res.route_reservations[0].reservation_state.value == "confirmed"


def test_incremental_commit_rolls_back_unreachable_candidate() -> None:
    inp, _goal = _strip_input()
    inp2 = OptimizationInput(
        asteroid_cells=inp.asteroid_cells,
        mineable_cells=inp.mineable_cells,
        rim_cells=inp.rim_cells,
        interior_cells=inp.interior_cells,
        external_void_cells=inp.external_void_cells,
        route_goals=frozenset(),
        existing_transport_cells=inp.existing_transport_cells,
        existing_trunk_cells=inp.existing_trunk_cells,
        protected_corridor_cells=inp.protected_corridor_cells,
        blocked_cells=inp.blocked_cells,
        topology_graph=inp.topology_graph,
        bbox=inp.bbox,
    )
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    g0 = RouteGoal(c2, RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    pool = (
        _bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=g0,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)
    res = commit_best_genome(genome, pool, inp2, RouteDomainSnapshotBuilder)
    assert res.confirmed_candidate_count == 0
    assert res.rolled_back_candidate_count == 1
    assert res.candidate_results[0].conflict_reason is CommitConflictReason.ROUTE_PROBE_FAILED


def test_incremental_commit_does_not_mutate_existing_confirmed_routes() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    b1 = _bundle(
        "ok",
        occupied=frozenset({c0}),
        output_stub=c1,
        transport_kind=TransportKind.SHAPE_BELT,
        probe_path=(c1, c2),
        goal=goal,
    )
    b2 = _bundle(
        "bad",
        occupied=frozenset({c2}),
        output_stub=c1,
        transport_kind=TransportKind.SHAPE_BELT,
        probe_path=(c1, c2),
        goal=goal,
    )
    genome = Genome("g", (Gene("ok", True, 0), Gene("bad", True, 1)), seed=0)
    n = 0

    def side(inp, *, occupied_cells=None):
        nonlocal n
        n += 1
        if n == 1:
            return real_run_route_probe(inp, occupied_cells=occupied_cells)
        return RouteProbeResult(
            reachable=False,
            path=(),
            cost=0,
            expanded_nodes=0,
            reached_goal=None,
            goal_priority=None,
            failure_reason=RouteProbeFailureReason.EXHAUSTED,
        )

    with patch(
        "django_apps.shapez_asteroid.optimization.incremental_commit.run_route_probe",
        side_effect=side,
    ):
        res = commit_best_genome(genome, (b1, b2), inp, RouteDomainSnapshotBuilder)
    assert len(res.route_reservations) == 1
    assert res.route_reservations[0].candidate_id == "ok"


def test_incremental_commit_transport_kind_conflict() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    shape = _bundle(
        "shape",
        occupied=frozenset({c0}),
        output_stub=c1,
        transport_kind=TransportKind.SHAPE_BELT,
        probe_path=(c1, c2),
        goal=goal,
    )
    fluid = _bundle(
        "fluid",
        occupied=frozenset({c2}),
        output_stub=c1,
        transport_kind=TransportKind.FLUID_PIPE,
        probe_path=(c1, c2),
        goal=goal,
    )
    genome = Genome("g", (Gene("shape", True, 0), Gene("fluid", True, 1)), seed=0)

    fake_path = (c1,)

    def fake_probe(inp, *, occupied_cells=None):
        _ = occupied_cells
        return RouteProbeResult(
            reachable=True,
            path=fake_path,
            cost=2,
            expanded_nodes=2,
            reached_goal=goal,
            goal_priority=0,
            failure_reason=None,
        )

    with patch(
        "django_apps.shapez_asteroid.optimization.incremental_commit.run_route_probe",
        side_effect=fake_probe,
    ):
        res = commit_best_genome(genome, (shape, fluid), inp, RouteDomainSnapshotBuilder)

    assert res.candidate_results[0].commit_state is PlacementCommitState.CONFIRMED
    assert res.candidate_results[1].conflict_reason is CommitConflictReason.TRANSPORT_KIND_CONFLICT


def test_incremental_commit_route_reservation_excludes_occupied_cells() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        _bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    occ = pool[0].occupied_cells
    assert not (res.route_reservations[0].reserved_cells & occ)


def test_incremental_commit_route_domain_reflects_prior_reservations() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    a = _bundle(
        "a",
        occupied=frozenset({c0}),
        output_stub=c1,
        transport_kind=TransportKind.SHAPE_BELT,
        probe_path=(c1, c2),
        goal=goal,
    )
    b = _bundle(
        "b",
        occupied=frozenset({c2}),
        output_stub=c1,
        transport_kind=TransportKind.SHAPE_BELT,
        probe_path=(c1, c2),
        goal=goal,
    )
    genome = Genome("g", (Gene("a", True, 0), Gene("b", True, 1)), seed=0)
    masks: list[int] = []

    def capture(inp, *, occupied_cells=None):
        _ = occupied_cells
        masks.append(inp.route_domain[c1].transport_mask.value)
        from django_apps.shapez_asteroid.optimization.route_probe import run_route_probe as real

        return real(inp, occupied_cells=occupied_cells)

    with patch(
        "django_apps.shapez_asteroid.optimization.incremental_commit.run_route_probe",
        side_effect=capture,
    ):
        commit_best_genome(genome, (a, b), inp, RouteDomainSnapshotBuilder)

    assert len(masks) == 2
    assert masks[0] != masks[1]


def test_incremental_commit_reservation_id_deterministic() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        _bundle(
            "x",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
        _bundle(
            "y",
            occupied=frozenset({c2}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("x", True, 0), Gene("y", True, 1)), seed=0)
    probes = (
        RouteProbeResult(
            reachable=True,
            path=(c1, c2),
            cost=2,
            expanded_nodes=2,
            reached_goal=goal,
            goal_priority=0,
            failure_reason=None,
        ),
        RouteProbeResult(
            reachable=True,
            path=(c1,),
            cost=1,
            expanded_nodes=1,
            reached_goal=goal,
            goal_priority=0,
            failure_reason=None,
        ),
    )
    n = 0

    def side(inp, *, occupied_cells=None):
        nonlocal n
        r = probes[n]
        n += 1
        return r

    with patch(
        "django_apps.shapez_asteroid.optimization.incremental_commit.run_route_probe",
        side_effect=side,
    ):
        res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    assert res.route_reservations[0].reservation_id == "x:route:0"
    assert res.route_reservations[1].reservation_id == "y:route:1"


def test_incremental_commit_uses_gene_commit_order_not_candidate_id() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    z = _bundle(
        "z",
        occupied=frozenset({c0}),
        output_stub=c1,
        transport_kind=TransportKind.SHAPE_BELT,
        probe_path=(c1, c2),
        goal=goal,
    )
    a = _bundle(
        "a",
        occupied=frozenset({c2}),
        output_stub=c1,
        transport_kind=TransportKind.SHAPE_BELT,
        probe_path=(c1,),
        goal=goal,
    )
    genome = Genome(
        "g",
        (
            Gene("z", True, commit_order=1),
            Gene("a", True, commit_order=0),
        ),
        seed=0,
    )
    order = [c.candidate_id for _, c in genome_commit_candidates(genome, (z, a))]
    assert order == ["a", "z"]


def test_incremental_commit_reprobes_latest_route_domain() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        _bundle(
            "p1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
        _bundle(
            "p2",
            occupied=frozenset({c2}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1,),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("p1", True, 0), Gene("p2", True, 1)), seed=0)
    ids: list[int] = []

    def cap(inp, *, occupied_cells=None):
        ids.append(id(inp.route_domain))
        from django_apps.shapez_asteroid.optimization.route_probe import run_route_probe as real

        return real(inp, occupied_cells=occupied_cells)

    with patch(
        "django_apps.shapez_asteroid.optimization.incremental_commit.run_route_probe",
        side_effect=cap,
    ):
        commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)

    assert len(ids) == 2
    assert ids[0] != ids[1]


def test_incremental_commit_failed_candidate_does_not_remove_prior_confirmed() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    ok = _bundle(
        "ok",
        occupied=frozenset({c0}),
        output_stub=c1,
        transport_kind=TransportKind.SHAPE_BELT,
        probe_path=(c1, c2),
        goal=goal,
    )
    bad = _bundle(
        "bad",
        occupied=frozenset({c2}),
        output_stub=c1,
        transport_kind=TransportKind.SHAPE_BELT,
        probe_path=(c1, c2),
        goal=goal,
    )
    genome = Genome("g", (Gene("ok", True, 0), Gene("bad", True, 1)), seed=0)
    res = commit_best_genome(genome, (ok, bad), inp, RouteDomainSnapshotBuilder)
    assert res.candidate_results[0].commit_state is PlacementCommitState.CONFIRMED
    assert res.candidate_results[1].commit_state is PlacementCommitState.ROLLED_BACK
    assert len(res.route_reservations) == 1


def test_incremental_commit_reserved_cells_match_path() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        _bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    r = res.route_reservations[0]
    assert r.reserved_cells == frozenset(r.path)


def test_incremental_commit_domain_cell_transitions_serialized() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        _bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    tr = res.route_reservations[0].domain_cell_transitions
    payload = [
        {
            "x": t.coord.x,
            "y": t.coord.y,
            "before": t.route_class_before.value,
            "after": t.route_class_after.value,
        }
        for t in tr
    ]
    json.dumps(payload)


def test_incremental_commit_conflict_reason_enum_only() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        _bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    for row in res.candidate_results:
        assert row.conflict_reason is None or isinstance(row.conflict_reason, CommitConflictReason)


def test_incremental_commit_shape_and_fluid_domains_separated() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    shape = _bundle(
        "shape",
        occupied=frozenset({c0}),
        output_stub=c1,
        transport_kind=TransportKind.SHAPE_BELT,
        probe_path=(c1, c2),
        goal=goal,
    )
    res = commit_best_genome(
        Genome("g", (Gene("shape", True, 0),), seed=0),
        (shape,),
        inp,
        RouteDomainSnapshotBuilder,
    )
    dom = res.final_route_domain
    for c in (c1, c2):
        assert dom[c].transport_mask is TransportMask.SHAPE_BELT


def test_incremental_commit_confirmed_occupied_cells_become_hard_blocked() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        _bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    assert res.final_route_domain[c0].hard_blocked is True


def test_incremental_commit_recovery_budget_exceeded() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        _bundle(
            "a",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
        _bundle(
            "b",
            occupied=frozenset({c2}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1,),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("a", True, 0), Gene("b", True, 1)), seed=0)
    budget = RecoveryBudget(max_removed_candidates=0, max_carve_cells=0, max_reroute_attempts=1)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder, recovery_budget=budget)
    assert res.candidate_results[0].commit_state is PlacementCommitState.CONFIRMED
    assert res.candidate_results[1].conflict_reason is CommitConflictReason.TRUNK_DEADLOCK


def test_incremental_commit_route_cell_conflict() -> None:
    """Cross-kind reuse of another candidate's reserved path cells (post mask-check)."""

    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    shape = _bundle(
        "shape",
        occupied=frozenset({c0}),
        output_stub=c1,
        transport_kind=TransportKind.SHAPE_BELT,
        probe_path=(c1, c2),
        goal=goal,
    )
    fluid_res = RouteReservation(
        reservation_id="fluid:route:0",
        candidate_id="fluid",
        transport_kind=TransportKind.FLUID_PIPE,
        path=(c1, c2),
        reserved_cells=frozenset({c1, c2}),
        cost=2,
        reached_goal=goal,
        goal_priority=0,
        reservation_state=ReservationState.CONFIRMED,
        domain_cell_transitions=(),
    )
    domain = {
        c1: RouteCellDomain(
            coord=c1,
            route_class=RouteClass.STANDARD,
            traversal_cost=1,
            hard_blocked=False,
            carve_allowed=False,
            transport_mask=TransportMask.BOTH,
        ),
        c2: RouteCellDomain(
            coord=c2,
            route_class=RouteClass.STANDARD,
            traversal_cost=1,
            hard_blocked=False,
            carve_allowed=False,
            transport_mask=TransportMask.BOTH,
        ),
    }
    reason = _path_conflict_reason(
        inp=inp,
        cand=shape,
        path=(c1, c2),
        route_domain=domain,
        committed_occupied=frozenset(),
        confirmed_reservations=(fluid_res,),
    )
    assert reason is CommitConflictReason.ROUTE_CELL_CONFLICT


def test_incremental_commit_hard_blocked_conflict() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    inp2 = OptimizationInput(
        asteroid_cells=inp.asteroid_cells,
        mineable_cells=inp.mineable_cells,
        rim_cells=inp.rim_cells,
        interior_cells=inp.interior_cells,
        external_void_cells=inp.external_void_cells,
        route_goals=inp.route_goals,
        existing_transport_cells=inp.existing_transport_cells,
        existing_trunk_cells=inp.existing_trunk_cells,
        protected_corridor_cells=inp.protected_corridor_cells,
        blocked_cells=frozenset({c2}),
        topology_graph=inp.topology_graph,
        bbox=inp.bbox,
    )
    pool = (
        _bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)

    def fake_probe(inp, *, occupied_cells=None):
        _ = occupied_cells
        return RouteProbeResult(
            reachable=True,
            path=(c1, c2),
            cost=2,
            expanded_nodes=2,
            reached_goal=goal,
            goal_priority=0,
            failure_reason=None,
        )

    with patch(
        "django_apps.shapez_asteroid.optimization.incremental_commit.run_route_probe",
        side_effect=fake_probe,
    ):
        res = commit_best_genome(genome, pool, inp2, RouteDomainSnapshotBuilder)

    assert res.candidate_results[0].conflict_reason is CommitConflictReason.HARD_BLOCKED_CONFLICT


def test_incremental_commit_occupied_cell_conflict_on_path() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (
        _bundle(
            "c1",
            occupied=frozenset({c0}),
            output_stub=c1,
            transport_kind=TransportKind.SHAPE_BELT,
            probe_path=(c1, c2),
            goal=goal,
        ),
    )
    genome = Genome("g", (Gene("c1", True, 0),), seed=0)

    def fake_probe(inp, *, occupied_cells=None):
        _ = occupied_cells
        return RouteProbeResult(
            reachable=True,
            path=(c0, c1, c2),
            cost=3,
            expanded_nodes=3,
            reached_goal=goal,
            goal_priority=0,
            failure_reason=None,
        )

    with patch(
        "django_apps.shapez_asteroid.optimization.incremental_commit.run_route_probe",
        side_effect=fake_probe,
    ):
        res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)

    assert res.candidate_results[0].conflict_reason is CommitConflictReason.OCCUPIED_CELL_CONFLICT
