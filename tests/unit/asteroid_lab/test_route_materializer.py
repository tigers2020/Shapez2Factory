"""Route network materialization tests (Solver Runtime PR6)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.commit_best_candidates import (
    ConfirmedGenePlacement,
    IncrementalCommitResult,
)
from django_apps.asteroid_lab.optimization.enums import (
    Direction,
    MaterializationFailureReason,
    PlacementCommitState,
    ReservationState,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal, RouteReservation
from django_apps.asteroid_lab.optimization.route_network_materializer import (
    full_path_for_reservation,
    materialize_route_network,
    pick_tile_type,
)
from django_apps.asteroid_lab.optimization.route_probe import RouteProbeResult


def _goal(*, coord: tuple[int, int], kind: TransportKind) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=kind,
        priority=10,
        existing_trunk=False,
    )


def _candidate(
    *,
    candidate_id: str,
    fixed_output_transport: tuple[int, int],
    path: tuple[tuple[int, int], ...],
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
) -> GeneCandidate:
    goal = _goal(coord=path[-1], kind=transport_kind)
    probe = RouteProbeResult(
        reachable=True,
        path=path,
        cost=len(path),
        expanded_nodes=len(path),
        reached_goal=goal,
        goal_priority=goal.priority,
        failure_reason=None,
    )
    return GeneCandidate(
        candidate_id=candidate_id,
        gene_id="test_gene",
        topology_signature="sig",
        extractor=(fixed_output_transport[0] - 1, fixed_output_transport[1]),
        extensions=(),
        occupied_cells=frozenset(),
        route_probe_start=path[0],
        fixed_output_transport=fixed_output_transport,
        output_dir=Direction.E,
        transport_kind=transport_kind,
        base_throughput=8,
        base_score=8.0,
        route_probe_result=probe,
    )


def _reservation(
    *,
    candidate_id: str,
    path: tuple[tuple[int, int], ...],
    transport_kind: TransportKind,
) -> RouteReservation:
    goal = _goal(coord=path[-1], kind=transport_kind)
    return RouteReservation(
        reservation_id=f"{candidate_id}:route:0",
        candidate_id=candidate_id,
        transport_kind=transport_kind,
        path=path,
        reserved_cells=frozenset(path),
        cost=len(path),
        reached_goal=goal,
        goal_priority=goal.priority,
        reservation_state=ReservationState.CONFIRMED,
        domain_cell_transitions=(),
    )


def _commit(
    placements: tuple[ConfirmedGenePlacement, ...],
) -> IncrementalCommitResult:
    return IncrementalCommitResult(
        confirmed=placements,
        skipped_candidate_ids=(),
        goal_assigned_platforms={},
    )


def _tile_map(result) -> dict[tuple[int, int], str]:
    assert result.layout is not None
    return {cell.coord: cell.tile_type for cell in result.layout.cells}


def test_full_path_prepends_fixed_output_transport() -> None:
    """OD-1: materialization path starts at fixed_output_transport."""

    fot = (1, 0)
    path = ((2, 0), (3, 0), (3, 1))
    candidate = _candidate(candidate_id="shape:od1", fixed_output_transport=fot, path=path)
    reservation = _reservation(
        candidate_id="shape:od1", path=path, transport_kind=TransportKind.SHAPE_BELT
    )

    full = full_path_for_reservation(candidate, reservation)

    assert full[0] == fot
    assert full[1:] == path


def test_full_path_dedupes_consecutive_duplicate() -> None:
    """OD-1: when FOT equals path[0], consecutive duplicate is removed once."""

    fot = (2, 0)
    path = ((2, 0), (3, 0), (3, 1))
    candidate = _candidate(candidate_id="shape:dedupe", fixed_output_transport=fot, path=path)
    reservation = _reservation(
        candidate_id="shape:dedupe", path=path, transport_kind=TransportKind.SHAPE_BELT
    )

    full = full_path_for_reservation(candidate, reservation)

    assert full == ((2, 0), (3, 0), (3, 1))


def test_route_materializer_creates_straight_and_turns() -> None:
    """East run then south turn; cells sorted by (sy, sx)."""

    cid = "shape:1"
    fot = (1, 0)
    path = ((2, 0), (3, 0), (3, 1))
    candidate = _candidate(candidate_id=cid, fixed_output_transport=fot, path=path)
    reservation = _reservation(candidate_id=cid, path=path, transport_kind=TransportKind.SHAPE_BELT)
    commit = _commit(
        (
            ConfirmedGenePlacement(
                candidate_id=cid,
                reservation=reservation,
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        )
    )

    result = materialize_route_network(commit, {cid: candidate})
    tiles = _tile_map(result)

    assert tiles[(1, 0)] == "SpaceBelt_Left"
    assert tiles[(2, 0)] == "SpaceBelt_Left"
    assert tiles[(3, 0)] == "SpaceBelt_LeftTurn"
    assert tiles[(3, 1)] == "SpaceBelt_Forward"


def test_route_materializer_merges_same_kind_shared_paths() -> None:
    """Two shape routes share trunk cell (2, 0) with 2-in-1-out flow."""

    c1_id = "shape:a"
    c2_id = "shape:b"
    path1 = ((1, 0), (2, 0), (3, 0))
    path2 = ((1, 2), (2, 2), (2, 1), (2, 0), (3, 0))
    cand1 = _candidate(candidate_id=c1_id, fixed_output_transport=(0, 0), path=path1)
    cand2 = _candidate(candidate_id=c2_id, fixed_output_transport=(0, 2), path=path2)
    commit = _commit(
        (
            ConfirmedGenePlacement(
                candidate_id=c1_id,
                reservation=_reservation(
                    candidate_id=c1_id, path=path1, transport_kind=TransportKind.SHAPE_BELT
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
            ConfirmedGenePlacement(
                candidate_id=c2_id,
                reservation=_reservation(
                    candidate_id=c2_id, path=path2, transport_kind=TransportKind.SHAPE_BELT
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        )
    )

    result = materialize_route_network(commit, {c1_id: cand1, c2_id: cand2})
    tiles = _tile_map(result)

    assert "Merger" in tiles[(2, 0)]
    assert tiles[(2, 0)] == "SpaceBelt_RightFwdMerger"


def test_route_materializer_rejects_shape_fluid_overlap() -> None:
    overlap = (2, 0)
    shape_path = ((1, 0), overlap, (3, 0))
    fluid_path = ((1, 2), (2, 2), overlap, (3, 0))
    shape_id = "shape:1"
    fluid_id = "fluid:1"
    shape = _candidate(
        candidate_id=shape_id,
        fixed_output_transport=(0, 0),
        path=shape_path,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    fluid = _candidate(
        candidate_id=fluid_id,
        fixed_output_transport=(0, 2),
        path=fluid_path,
        transport_kind=TransportKind.FLUID_PIPE,
    )
    commit = _commit(
        (
            ConfirmedGenePlacement(
                candidate_id=shape_id,
                reservation=_reservation(
                    candidate_id=shape_id,
                    path=shape_path,
                    transport_kind=TransportKind.SHAPE_BELT,
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
            ConfirmedGenePlacement(
                candidate_id=fluid_id,
                reservation=_reservation(
                    candidate_id=fluid_id,
                    path=fluid_path,
                    transport_kind=TransportKind.FLUID_PIPE,
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        )
    )

    result = materialize_route_network(commit, {shape_id: shape, fluid_id: fluid})

    assert result.layout is None
    assert result.failure_reason == MaterializationFailureReason.TRANSPORT_KIND_OVERLAP


def test_route_materializer_selects_y_or_triple_merger() -> None:
    triple_center = (0, 0)

    triple_paths = (
        ((0, -1), triple_center, (1, 0)),
        ((-1, 0), triple_center, (1, 0)),
        ((1, 0), triple_center),
    )

    assert (
        pick_tile_type(
            TransportKind.SHAPE_BELT,
            frozenset({Direction.N, Direction.W, Direction.E}),
            frozenset({Direction.E}),
        )
        == "SpaceBelt_TripleMerger"
    )
    assert (
        pick_tile_type(
            TransportKind.SHAPE_BELT,
            frozenset({Direction.N, Direction.S, Direction.W}),
            frozenset({Direction.E}),
        )
        == "SpaceBelt_YMerger"
    )

    triple_flow = pick_tile_type(
        TransportKind.SHAPE_BELT,
        frozenset({Direction.N, Direction.W, Direction.E}),
        frozenset({Direction.E}),
    )
    y_flow = pick_tile_type(
        TransportKind.SHAPE_BELT,
        frozenset({Direction.N, Direction.S, Direction.W}),
        frozenset({Direction.E}),
    )
    assert triple_flow == "SpaceBelt_TripleMerger"
    assert y_flow == "SpaceBelt_YMerger"

    def _triple_commit() -> IncrementalCommitResult:
        placements: list[ConfirmedGenePlacement] = []
        candidates: dict[str, GeneCandidate] = {}
        for i, p in enumerate(triple_paths):
            cid = f"triple:{i}"
            fot = p[0]
            probe_path = p[1:]
            cand = _candidate(candidate_id=cid, fixed_output_transport=fot, path=probe_path)
            candidates[cid] = cand
            placements.append(
                ConfirmedGenePlacement(
                    candidate_id=cid,
                    reservation=_reservation(
                        candidate_id=cid,
                        path=probe_path,
                        transport_kind=TransportKind.SHAPE_BELT,
                    ),
                    commit_state=PlacementCommitState.CONFIRMED,
                )
            )
        return _commit(tuple(placements)), candidates

    triple_commit_result, triple_candidates = _triple_commit()
    triple_tiles = _tile_map(materialize_route_network(triple_commit_result, triple_candidates))
    assert triple_tiles[triple_center] == "SpaceBelt_TripleMerger"


def test_route_materializer_splits_shared_trunk() -> None:
    """Two shape routes: hub (2, 0) has 1-in (W) / 2-out (E, N) → forward splitter."""

    trunk_id = "shape:trunk"
    branch_id = "shape:branch"
    hub = (2, 0)
    trunk_path = ((1, 0), hub, (3, 0))
    branch_path = ((2, 1),)
    trunk = _candidate(candidate_id=trunk_id, fixed_output_transport=(0, 0), path=trunk_path)
    branch = _candidate(candidate_id=branch_id, fixed_output_transport=hub, path=branch_path)
    commit = _commit(
        (
            ConfirmedGenePlacement(
                candidate_id=trunk_id,
                reservation=_reservation(
                    candidate_id=trunk_id,
                    path=trunk_path,
                    transport_kind=TransportKind.SHAPE_BELT,
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
            ConfirmedGenePlacement(
                candidate_id=branch_id,
                reservation=_reservation(
                    candidate_id=branch_id,
                    path=branch_path,
                    transport_kind=TransportKind.SHAPE_BELT,
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        )
    )

    result = materialize_route_network(commit, {trunk_id: trunk, branch_id: branch})
    tiles = _tile_map(result)

    assert "Splitter" in tiles[hub]
    assert tiles[hub] == "SpaceBelt_LeftFwdSplitter"


def test_route_materializer_selects_triple_splitter_at_hub() -> None:
    """Hub (2, 0): W in, E/W/N out → triple splitter (opposite-arm triple pattern)."""

    hub = (2, 0)
    trunk_id = "shape:trunk"
    trunk_path = ((1, 0), hub, (3, 0))
    trunk = _candidate(candidate_id=trunk_id, fixed_output_transport=(0, 0), path=trunk_path)
    west_id = "shape:west"
    west_path = ((1, 0),)
    west = _candidate(candidate_id=west_id, fixed_output_transport=hub, path=west_path)
    north_id = "shape:north"
    north_path = ((2, 1),)
    north = _candidate(candidate_id=north_id, fixed_output_transport=hub, path=north_path)

    assert (
        pick_tile_type(
            TransportKind.SHAPE_BELT,
            frozenset({Direction.W}),
            frozenset({Direction.E, Direction.W, Direction.N}),
        )
        == "SpaceBelt_TripleSplitter"
    )

    commit = _commit(
        (
            ConfirmedGenePlacement(
                candidate_id=trunk_id,
                reservation=_reservation(
                    candidate_id=trunk_id,
                    path=trunk_path,
                    transport_kind=TransportKind.SHAPE_BELT,
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
            ConfirmedGenePlacement(
                candidate_id=west_id,
                reservation=_reservation(
                    candidate_id=west_id,
                    path=west_path,
                    transport_kind=TransportKind.SHAPE_BELT,
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
            ConfirmedGenePlacement(
                candidate_id=north_id,
                reservation=_reservation(
                    candidate_id=north_id,
                    path=north_path,
                    transport_kind=TransportKind.SHAPE_BELT,
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        )
    )
    tiles = _tile_map(
        materialize_route_network(commit, {trunk_id: trunk, west_id: west, north_id: north})
    )
    assert tiles[hub] == "SpaceBelt_TripleSplitter"


def test_route_materializer_cell_order_is_deterministic() -> None:
    cid = "shape:det"
    fot = (1, 0)
    path = ((2, 0), (3, 0), (3, 1))
    candidate = _candidate(candidate_id=cid, fixed_output_transport=fot, path=path)
    commit = _commit(
        (
            ConfirmedGenePlacement(
                candidate_id=cid,
                reservation=_reservation(
                    candidate_id=cid, path=path, transport_kind=TransportKind.SHAPE_BELT
                ),
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        )
    )
    candidates = {cid: candidate}

    first = materialize_route_network(commit, candidates)
    second = materialize_route_network(commit, candidates)

    assert first.layout is not None
    assert second.layout is not None
    assert first.layout.cells == second.layout.cells
