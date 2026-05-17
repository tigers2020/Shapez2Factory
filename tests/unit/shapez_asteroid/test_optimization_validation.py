"""Sequence 7 — final validation gate for incremental commit results."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.optimization.coords import BBox, Coord
from django_apps.shapez_asteroid.optimization.dto import (
    BundleCandidate,
    CommittedPlacement,
    IncrementalCommitResult,
    OptimizationInput,
    RouteCellDomain,
    RouteGoal,
    RouteProbeResult,
    RouteReservation,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
    ValidationIssue,
    ValidationIssueCode,
    ValidationSeverity,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CardinalDirection,
    EdgeKind,
    ReservationState,
    RouteGoalKind,
    TopologyNodeKind,
    TransportKind,
    TransportMask,
)
from django_apps.shapez_asteroid.optimization.final_validation import (
    _sort_issues,
    validate_incremental_commit_result,
    validation_passed_from_issues,
)
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
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


def _strip_input4() -> tuple[OptimizationInput, RouteGoal]:
    c0, c1, c2, c3 = Coord(0, 0), Coord(1, 0), Coord(2, 0), Coord(3, 0)
    coords = (c0, c1, c2, c3)
    ac = frozenset(coords)
    rim = frozenset({c0, c3})
    mineable = ac
    interior = frozenset({c1, c2})
    ext_void: frozenset[Coord] = frozenset()
    goal = RouteGoal(c3, RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    bbox = BBox(0, 3, 0, 0)
    nodes = frozenset(
        TopologyNode(coord=c, node_kind=TopologyNodeKind.EXTERNAL_VOID) for c in coords
    )
    edges = frozenset({_canon_edge(c0, c1), _canon_edge(c1, c2), _canon_edge(c2, c3)})
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


def _candidate(
    cid: str,
    *,
    occupied: frozenset[Coord],
    output_stub: Coord,
    path: tuple[Coord, ...],
    goal: RouteGoal,
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
    extensions: tuple[Coord, ...] | None = None,
) -> BundleCandidate:
    extractor = min(occupied, key=lambda z: (z.x, z.y))
    exts = (
        extensions
        if extensions is not None
        else tuple(sorted(occupied - {extractor}, key=lambda z: (z.x, z.y)))
    )
    return BundleCandidate(
        candidate_id=cid,
        pattern_id="p",
        topology_signature="sig",
        extractor=extractor,
        extensions=exts,
        occupied_cells=occupied,
        output_stub=output_stub,
        output_dir=CardinalDirection.EAST,
        transport_kind=transport_kind,
        base_throughput=1,
        base_score=1.0,
        route_probe_result=_ok_probe(path, goal),
    )


def _reservation(
    rid: str,
    cid: str,
    path: tuple[Coord, ...],
    goal: RouteGoal,
    *,
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
    reserved_cells: frozenset[Coord] | None = None,
    state: ReservationState = ReservationState.CONFIRMED,
) -> RouteReservation:
    rs = reserved_cells if reserved_cells is not None else frozenset(path)
    return RouteReservation(
        reservation_id=rid,
        candidate_id=cid,
        transport_kind=transport_kind,
        path=path,
        reserved_cells=rs,
        cost=len(path),
        reached_goal=goal,
        goal_priority=goal.priority,
        reservation_state=state,
        domain_cell_transitions=(),
    )


def _commit_one(
    inp: OptimizationInput,
    placement: CommittedPlacement,
    res: RouteReservation,
) -> IncrementalCommitResult:
    dom = RouteDomainSnapshotBuilder.build_snapshot(
        inp,
        confirmed_reservations=(res,),
        committed_occupied_cells=placement.occupied_cells,
    )
    return IncrementalCommitResult(
        committed_placements=(placement,),
        route_reservations=(res,),
        candidate_results=(),
        final_route_domain=dom,
        confirmed_candidate_count=1,
        rolled_back_candidate_count=0,
    )


def test_validation_passes_connected_layout() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c1, path=path, goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    res = _reservation("a:route:0", "a", path, goal)
    commit = _commit_one(inp, pl, res)
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert vr.passed is True
    assert vr.issues == ()


def test_validation_fails_unconnected_extractor() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c1, path=path, goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    bad_path = (c0, c1, c2)
    res = _reservation("a:route:0", "a", bad_path, goal)
    commit = _commit_one(inp, pl, res)
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert vr.passed is False
    assert any(i.issue_code is ValidationIssueCode.EXTRACTOR_OUTPUT_DISCONNECTED for i in vr.issues)


def test_validation_fails_orphan_transport() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c1, path=path, goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    res_ok = _reservation("a:route:0", "a", path, goal)
    orphan = _reservation("ghost:route:1", "ghost", path, goal)
    dom = RouteDomainSnapshotBuilder.build_snapshot(
        inp,
        confirmed_reservations=(res_ok, orphan),
        committed_occupied_cells=pl.occupied_cells,
    )
    commit = IncrementalCommitResult(
        committed_placements=(pl,),
        route_reservations=(res_ok, orphan),
        candidate_results=(),
        final_route_domain=dom,
        confirmed_candidate_count=1,
        rolled_back_candidate_count=0,
    )
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert vr.passed is False
    assert any(i.issue_code is ValidationIssueCode.ORPHAN_TRANSPORT for i in vr.issues)


def test_validation_fails_invalid_coord_contract() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    bad = BundleCandidate(
        candidate_id="a",
        pattern_id="p",
        topology_signature="sig",
        extractor=c0,
        extensions=(),
        occupied_cells=frozenset({c0}),
        output_stub=c1,
        output_dir=CardinalDirection.EAST,
        transport_kind=TransportKind.SHAPE_BELT,
        base_throughput=1,
        base_score=1.0,
        route_probe_result=_ok_probe((c1, c2), goal),
    )
    pool = (bad,)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({Coord(0.0, 0)}),  # type: ignore[arg-type]
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    path = (c1, c2)
    res = _reservation("a:route:0", "a", path, goal)
    commit = _commit_one(inp, pl, res)
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert vr.passed is False
    assert any(i.issue_code is ValidationIssueCode.INVALID_COORD_CONTRACT for i in vr.issues)


def test_validation_read_only() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c1, path=path, goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    res = _reservation("a:route:0", "a", path, goal)
    commit = _commit_one(inp, pl, res)
    before = id(commit.final_route_domain)
    validate_incremental_commit_result(inp, pool, commit)
    assert id(commit.final_route_domain) == before


def test_validation_issue_codes_explicit() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c1, path=(c1, c2), goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="wrong-id",
    )
    res = _reservation("a:route:0", "a", (c1, c2), goal)
    commit = _commit_one(inp, pl, res)
    vr = validate_incremental_commit_result(inp, pool, commit)
    codes = {i.issue_code for i in vr.issues}
    assert ValidationIssueCode.CONFIRMED_RESERVATION_MISSING in codes


def test_validation_issue_includes_route_goal_and_transport_context() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    other = RouteGoal(c1, RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c1, path=(c1, c2), goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    path = (c1, c2)
    res = _reservation("a:route:0", "a", path, other)
    commit = _commit_one(inp, pl, res)
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert vr.passed is False
    mismatch = [i for i in vr.issues if i.issue_code is ValidationIssueCode.ROUTE_GOAL_MISMATCH]
    assert mismatch
    assert mismatch[0].route_goal_kind is not None
    assert mismatch[0].transport_kind is not None or mismatch[0].route_goal_kind == other.goal_kind


def test_validation_fails_candidate_without_confirmed_reservation() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c1, path=(c1, c2), goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    res = _reservation("a:route:0", "a", (c1, c2), goal, state=ReservationState.PROVISIONAL)
    commit = _commit_one(inp, pl, res)
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert vr.passed is False
    assert any(i.issue_code is ValidationIssueCode.CONFIRMED_RESERVATION_MISSING for i in vr.issues)


def test_validation_fails_reserved_cells_path_mismatch() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c1, path=path, goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    res = _reservation("a:route:0", "a", path, goal, reserved_cells=frozenset({c2}))
    commit = _commit_one(inp, pl, res)
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert any(i.issue_code is ValidationIssueCode.RESERVED_PATH_MISMATCH for i in vr.issues)


def test_validation_fails_transport_kind_mismatch() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    pool = (
        _candidate(
            "a",
            occupied=frozenset({c0}),
            output_stub=c1,
            path=path,
            goal=goal,
            transport_kind=TransportKind.SHAPE_BELT,
        ),
    )
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.FLUID_PIPE,
        route_reservation_id="a:route:0",
    )
    res = _reservation("a:route:0", "a", path, goal, transport_kind=TransportKind.SHAPE_BELT)
    commit = _commit_one(inp, pl, res)
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert any(i.issue_code is ValidationIssueCode.TRANSPORT_KIND_MISMATCH for i in vr.issues)


def test_validation_fails_invalid_overlap_between_placements() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    share = c1
    pool = (
        _candidate("a", occupied=frozenset({c0, share}), output_stub=c2, path=(c2,), goal=goal),
        _candidate("b", occupied=frozenset({share}), output_stub=c2, path=(c2,), goal=goal),
    )
    # invalid geometry for real routing; only testing placement overlap detection
    pl_a = CommittedPlacement("a", frozenset({c0, share}), TransportKind.SHAPE_BELT, "a:0")
    pl_b = CommittedPlacement("b", frozenset({share}), TransportKind.SHAPE_BELT, "b:0")
    res_a = _reservation("a:0", "a", (c2,), goal)
    res_b = _reservation("b:0", "b", (c2,), goal)
    dom = RouteDomainSnapshotBuilder.build_snapshot(
        inp,
        confirmed_reservations=(res_a, res_b),
        committed_occupied_cells=pl_a.occupied_cells | pl_b.occupied_cells,
    )
    commit = IncrementalCommitResult(
        committed_placements=(pl_a, pl_b),
        route_reservations=(res_a, res_b),
        candidate_results=(),
        final_route_domain=dom,
        confirmed_candidate_count=2,
        rolled_back_candidate_count=0,
    )
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert any(i.issue_code is ValidationIssueCode.INVALID_OVERLAP for i in vr.issues)


def test_validation_fails_route_path_through_placement() -> None:
    inp, goal = _strip_input4()
    c0, c1, c2, c3 = Coord(0, 0), Coord(1, 0), Coord(2, 0), Coord(3, 0)
    pool = (
        _candidate("a", occupied=frozenset({c0}), output_stub=c1, path=(c1, c2, c3), goal=goal),
        _candidate("b", occupied=frozenset({c2}), output_stub=c1, path=(c1, c3), goal=goal),
    )
    pl_a = CommittedPlacement("a", frozenset({c0}), TransportKind.SHAPE_BELT, "a:0")
    pl_b = CommittedPlacement("b", frozenset({c2}), TransportKind.SHAPE_BELT, "b:0")
    path_a = (c1, c2, c3)
    res_a = _reservation("a:0", "a", path_a, goal)
    res_b = _reservation("b:0", "b", (c1, c3), goal)
    dom = RouteDomainSnapshotBuilder.build_snapshot(
        inp,
        confirmed_reservations=(res_a, res_b),
        committed_occupied_cells=pl_a.occupied_cells | pl_b.occupied_cells,
    )
    commit = IncrementalCommitResult(
        committed_placements=(pl_a, pl_b),
        route_reservations=(res_a, res_b),
        candidate_results=(),
        final_route_domain=dom,
        confirmed_candidate_count=2,
        rolled_back_candidate_count=0,
    )
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert any(
        i.issue_code is ValidationIssueCode.INVALID_OVERLAP
        and i.coord == c2
        and i.candidate_id == "a"
        for i in vr.issues
    )


def test_validation_fails_output_stub_not_path_start() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c2, path=(c1, c2), goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    res = _reservation("a:route:0", "a", (c1, c2), goal)
    commit = _commit_one(inp, pl, res)
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert any(i.issue_code is ValidationIssueCode.EXTRACTOR_OUTPUT_DISCONNECTED for i in vr.issues)


def test_validation_warning_info_do_not_fail_if_added() -> None:
    warn = ValidationIssue(
        issue_code=ValidationIssueCode.ORPHAN_TRANSPORT,
        severity=ValidationSeverity.WARNING,
        coord=None,
        candidate_id=None,
        route_reservation_id=None,
        path_index=None,
        route_goal_kind=None,
        transport_kind=None,
        message="synthetic",
    )
    info = ValidationIssue(
        issue_code=ValidationIssueCode.ORPHAN_TRANSPORT,
        severity=ValidationSeverity.INFO,
        coord=None,
        candidate_id=None,
        route_reservation_id=None,
        path_index=None,
        route_goal_kind=None,
        transport_kind=None,
        message="synthetic2",
    )
    assert validation_passed_from_issues((warn, info)) is True


def test_validation_uses_server_dense_coord_contract_x_zero_allowed() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c1, path=path, goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    res = _reservation("a:route:0", "a", path, goal)
    commit = _commit_one(inp, pl, res)
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert not any(i.issue_code is ValidationIssueCode.INVALID_COORD_CONTRACT for i in vr.issues)


def test_validation_does_not_call_route_probe() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c1, path=path, goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    res = _reservation("a:route:0", "a", path, goal)
    commit = _commit_one(inp, pl, res)

    def boom(*_a: object, **_k: object) -> None:
        raise AssertionError("run_route_probe must not be called by final validation")

    with patch(
        "django_apps.shapez_asteroid.optimization.route_probe.run_route_probe", side_effect=boom
    ):
        vr = validate_incremental_commit_result(inp, pool, commit)
    assert vr.passed is True


def test_validation_does_not_mutate_commit_result() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c1, path=path, goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    res = _reservation("a:route:0", "a", path, goal)
    commit = _commit_one(inp, pl, res)
    snap = (
        tuple(commit.committed_placements),
        tuple(commit.route_reservations),
        id(commit.final_route_domain),
        len(commit.final_route_domain),
    )
    validate_incremental_commit_result(inp, pool, commit)
    snap2 = (
        tuple(commit.committed_placements),
        tuple(commit.route_reservations),
        id(commit.final_route_domain),
        len(commit.final_route_domain),
    )
    assert snap == snap2


def test_validation_issues_sorted_deterministically() -> None:
    a = ValidationIssue(
        issue_code=ValidationIssueCode.RESERVED_PATH_MISMATCH,
        severity=ValidationSeverity.ERROR,
        coord=None,
        candidate_id="z",
        route_reservation_id=None,
        path_index=None,
        route_goal_kind=None,
        transport_kind=None,
        message="m2",
    )
    b = ValidationIssue(
        issue_code=ValidationIssueCode.INVALID_COORD_CONTRACT,
        severity=ValidationSeverity.ERROR,
        coord=None,
        candidate_id="a",
        route_reservation_id=None,
        path_index=None,
        route_goal_kind=None,
        transport_kind=None,
        message="m1",
    )
    out = _sort_issues((a, b))
    assert [i.issue_code for i in out] == [
        ValidationIssueCode.INVALID_COORD_CONTRACT,
        ValidationIssueCode.RESERVED_PATH_MISMATCH,
    ]


def test_duplicate_candidate_id_raises() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    c = _candidate("dup", occupied=frozenset({c0}), output_stub=c1, path=(c1, c2), goal=goal)
    pool = (c, c)
    pl = CommittedPlacement(
        candidate_id="dup",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="dup:0",
    )
    res = _reservation("dup:0", "dup", (c1, c2), goal)
    commit = _commit_one(inp, pl, res)
    with pytest.raises(ValueError, match="duplicate candidate_id"):
        validate_incremental_commit_result(inp, pool, commit)


def test_validation_fails_route_domain_transport_mask() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    pool = (
        _candidate(
            "a",
            occupied=frozenset({c0}),
            output_stub=c1,
            path=path,
            goal=goal,
            transport_kind=TransportKind.FLUID_PIPE,
        ),
    )
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.FLUID_PIPE,
        route_reservation_id="a:route:0",
    )
    res = _reservation("a:route:0", "a", path, goal, transport_kind=TransportKind.FLUID_PIPE)
    dom = dict(
        RouteDomainSnapshotBuilder.build_snapshot(
            inp, confirmed_reservations=(res,), committed_occupied_cells=pl.occupied_cells
        )
    )
    dom[c1] = RouteCellDomain(
        coord=c1,
        route_class=dom[c1].route_class,
        traversal_cost=dom[c1].traversal_cost,
        hard_blocked=dom[c1].hard_blocked,
        carve_allowed=dom[c1].carve_allowed,
        transport_mask=TransportMask.SHAPE_BELT,
    )
    commit = IncrementalCommitResult(
        committed_placements=(pl,),
        route_reservations=(res,),
        candidate_results=(),
        final_route_domain=dom,
        confirmed_candidate_count=1,
        rolled_back_candidate_count=0,
    )
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert any(i.issue_code is ValidationIssueCode.TRANSPORT_KIND_MISMATCH for i in vr.issues)


def test_validation_fails_extension_constraints() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    occupied = frozenset({c0, c1})
    pool = (
        BundleCandidate(
            candidate_id="a",
            pattern_id="p",
            topology_signature="sig",
            extractor=c0,
            extensions=(c1, c2, c2, c0),
            occupied_cells=occupied,
            output_stub=c1,
            output_dir=CardinalDirection.EAST,
            transport_kind=TransportKind.SHAPE_BELT,
            base_throughput=1,
            base_score=1.0,
            route_probe_result=_ok_probe(path, goal),
        ),
    )
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=occupied,
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    res = _reservation("a:route:0", "a", path, goal)
    commit = _commit_one(inp, pl, res)
    vr = validate_incremental_commit_result(inp, pool, commit)
    codes = {i.issue_code for i in vr.issues}
    assert (
        ValidationIssueCode.EXTENSION_COUNT_EXCEEDED in codes
        or ValidationIssueCode.EXTENSION_ATTACHMENT_INVALID in codes
    )


def test_validate_coord_contract_safe_sort_malformed_cell_no_raise() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    pool = (_candidate("a", occupied=frozenset({c0}), output_stub=c1, path=path, goal=goal),)
    pl = CommittedPlacement(
        candidate_id="a",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="a:route:0",
    )
    res = _reservation("a:route:0", "a", path, goal)
    commit = _commit_one(inp, pl, res)

    class NonCoord:
        def __repr__(self) -> str:
            return "NonCoord"

    inp_bad = replace(
        inp,
        asteroid_cells=frozenset({NonCoord(), c0}),  # type: ignore[arg-type]
    )
    vr = validate_incremental_commit_result(inp_bad, pool, commit)
    assert any(i.issue_code is ValidationIssueCode.INVALID_COORD_CONTRACT for i in vr.issues)


def test_validation_fails_committed_candidate_missing_from_pool() -> None:
    inp, goal = _strip_input()
    c0, c1, c2 = Coord(0, 0), Coord(1, 0), Coord(2, 0)
    path = (c1, c2)
    pool = (_candidate("other", occupied=frozenset({c0}), output_stub=c1, path=path, goal=goal),)
    pl = CommittedPlacement(
        candidate_id="missing",
        occupied_cells=frozenset({c0}),
        transport_kind=TransportKind.SHAPE_BELT,
        route_reservation_id="missing:0",
    )
    res = _reservation("missing:0", "missing", path, goal)
    commit = _commit_one(inp, pl, res)
    vr = validate_incremental_commit_result(inp, pool, commit)
    assert any(i.issue_code is ValidationIssueCode.CANDIDATE_POOL_MISSING for i in vr.issues)
