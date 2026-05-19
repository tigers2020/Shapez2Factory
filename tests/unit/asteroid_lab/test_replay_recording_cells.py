"""Unit tests for replay_recording_cells helpers (output-only; no ORM)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.commit_best_candidates import ConfirmedGenePlacement
from django_apps.asteroid_lab.optimization.enums import (
    Direction,
    PlacementCommitState,
    ReservationState,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal, RouteReservation
from django_apps.asteroid_lab.optimization.loaded_snapshot import LoadedReconstructionSnapshot
from django_apps.asteroid_lab.optimization.materialization_dtos import (
    MaterializedLayoutCells,
    MaterializedTransportCell,
    RouteMaterializationResult,
)
from django_apps.asteroid_lab.optimization.route_probe import RouteProbeResult
from django_apps.asteroid_lab.replay.replay_recording_cells import (
    full_cell_dicts_from_final_replay_state,
    miner_cell_dicts_from_confirmed,
    overlay_cell_dicts_from_materialization,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO

# ---------------------------------------------------------------------------
# Minimal fixture helpers
# ---------------------------------------------------------------------------

_VALID_GOAL = RouteGoal(
    coord=(6, 0),
    goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
    transport_kind=TransportKind.SHAPE_BELT,
    priority=10,
    existing_trunk=False,
)


def _mat_cell(coord: tuple[int, int], tk: TransportKind) -> MaterializedTransportCell:
    return MaterializedTransportCell(coord=coord, tile_type="", transport_kind=tk, rotation=0)


def _mat_result(*cells: MaterializedTransportCell) -> RouteMaterializationResult:
    return RouteMaterializationResult(
        layout=MaterializedLayoutCells(cells=tuple(cells)),
        failure_reason=None,
    )


def _gene_candidate(
    *,
    candidate_id: str,
    extractor: tuple[int, int],
    extensions: tuple[tuple[int, int], ...] = (),
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
) -> GeneCandidate:
    probe = RouteProbeResult(
        reachable=True,
        path=(),
        cost=0,
        expanded_nodes=0,
        reached_goal=_VALID_GOAL,
        goal_priority=10,
        failure_reason=None,
    )
    return GeneCandidate(
        candidate_id=candidate_id,
        gene_id="g",
        topology_signature="sig",
        extractor=extractor,
        extensions=extensions,
        occupied_cells=frozenset({extractor, *extensions}),
        route_probe_start=extractor,
        fixed_output_transport=(extractor[0] + 1, extractor[1]),
        output_dir=Direction.E,
        transport_kind=transport_kind,
        base_throughput=8,
        base_score=8.0,
        route_probe_result=probe,
    )


def _confirmed(candidate: GeneCandidate) -> ConfirmedGenePlacement:
    res = RouteReservation(
        reservation_id=f"{candidate.candidate_id}:r",
        candidate_id=candidate.candidate_id,
        transport_kind=candidate.transport_kind,
        path=(),
        reserved_cells=frozenset(),
        cost=0,
        reached_goal=_VALID_GOAL,
        goal_priority=10,
        reservation_state=ReservationState.CONFIRMED,
        domain_cell_transitions=(),
    )
    return ConfirmedGenePlacement(
        candidate_id=candidate.candidate_id,
        reservation=res,
        commit_state=PlacementCommitState.CONFIRMED,
    )


# ---------------------------------------------------------------------------
# overlay_cell_dicts_from_materialization
# ---------------------------------------------------------------------------


def test_materialization_shape_belt_uses_space_belt_cell_kind() -> None:
    result = _mat_result(_mat_cell((3, 4), TransportKind.SHAPE_BELT))
    rows = overlay_cell_dicts_from_materialization(result)
    assert len(rows) == 1
    assert rows[0]["cell_kind"] == "space_belt"
    assert rows[0]["transport_kind"] == "shape_belt"
    assert rows[0]["server_x"] == 3
    assert rows[0]["server_y"] == 4


def _mat_cell_with_tile(
    coord: tuple[int, int],
    tk: TransportKind,
    tile_type: str,
    rotation: int,
) -> MaterializedTransportCell:
    return MaterializedTransportCell(
        coord=coord, tile_type=tile_type, transport_kind=tk, rotation=rotation
    )


def test_materialization_overlay_includes_tile_type_and_rotation() -> None:
    """overlay_cell_dicts must carry tile_type and rotation for JS sprite lookup."""
    cell = _mat_cell_with_tile((2, 0), TransportKind.SHAPE_BELT, "SpaceBelt_Forward", 0)
    rows = overlay_cell_dicts_from_materialization(_mat_result(cell))
    assert len(rows) == 1
    assert rows[0]["tile_type"] == "SpaceBelt_Forward"
    assert rows[0]["rotation"] == 0


def test_materialization_overlay_rotation_non_zero() -> None:
    """Rotation values other than 0 must be preserved through the wire."""
    cell = _mat_cell_with_tile((1, 1), TransportKind.SHAPE_BELT, "SpaceBelt_LeftTurn", 1)
    rows = overlay_cell_dicts_from_materialization(_mat_result(cell))
    assert rows[0]["tile_type"] == "SpaceBelt_LeftTurn"
    assert rows[0]["rotation"] == 1


def test_materialization_overlay_pipe_tile_type_preserved() -> None:
    cell = _mat_cell_with_tile((0, 0), TransportKind.FLUID_PIPE, "SpacePipe_RightTurn", 2)
    rows = overlay_cell_dicts_from_materialization(_mat_result(cell))
    assert rows[0]["tile_type"] == "SpacePipe_RightTurn"
    assert rows[0]["rotation"] == 2


def test_materialization_fluid_pipe_uses_space_pipe_cell_kind() -> None:
    result = _mat_result(_mat_cell((1, 2), TransportKind.FLUID_PIPE))
    rows = overlay_cell_dicts_from_materialization(result)
    assert len(rows) == 1
    assert rows[0]["cell_kind"] == "space_pipe"
    assert rows[0]["transport_kind"] == "fluid_pipe"


def test_materialization_no_route_materialized_sentinel() -> None:
    """``route_materialized`` string must never appear — it has no JS tone mapping."""
    cells = [
        _mat_cell((0, 0), TransportKind.SHAPE_BELT),
        _mat_cell((1, 0), TransportKind.FLUID_PIPE),
    ]
    rows = overlay_cell_dicts_from_materialization(_mat_result(*cells))
    for row in rows:
        assert row["cell_kind"] != "route_materialized"


def test_materialization_empty_layout_returns_empty() -> None:
    result = RouteMaterializationResult(layout=None, failure_reason=None)
    assert overlay_cell_dicts_from_materialization(result) == ()


def test_materialization_multiple_cells_all_mapped() -> None:
    cells = [_mat_cell((i, 0), TransportKind.SHAPE_BELT) for i in range(5)]
    rows = overlay_cell_dicts_from_materialization(_mat_result(*cells))
    assert len(rows) == 5
    assert all(r["cell_kind"] == "space_belt" for r in rows)


# ---------------------------------------------------------------------------
# miner_cell_dicts_from_confirmed
# ---------------------------------------------------------------------------


def test_miner_shape_belt_extractor_uses_shape_miner_kind() -> None:
    c = _gene_candidate(candidate_id="a", extractor=(5, 3))
    rows = miner_cell_dicts_from_confirmed((_confirmed(c),), {c.candidate_id: c})
    assert len(rows) == 1
    assert rows[0]["cell_kind"] == "shape_miner"
    assert rows[0]["server_x"] == 5
    assert rows[0]["server_y"] == 3


def test_miner_fluid_pipe_extractor_uses_fluid_miner_kind() -> None:
    c = _gene_candidate(candidate_id="b", extractor=(2, 7), transport_kind=TransportKind.FLUID_PIPE)
    rows = miner_cell_dicts_from_confirmed((_confirmed(c),), {c.candidate_id: c})
    assert len(rows) == 1
    assert rows[0]["cell_kind"] == "fluid_miner"


def test_miner_extensions_use_extension_kind() -> None:
    c = _gene_candidate(
        candidate_id="c",
        extractor=(0, 0),
        extensions=((0, 1), (0, 2)),
    )
    rows = miner_cell_dicts_from_confirmed((_confirmed(c),), {c.candidate_id: c})
    assert len(rows) == 3  # extractor + 2 extensions
    kinds = {r["cell_kind"] for r in rows}
    assert kinds == {"shape_miner", "shape_miner_extension"}


def test_miner_fluid_extensions_use_fluid_extension_kind() -> None:
    c = _gene_candidate(
        candidate_id="d",
        extractor=(1, 1),
        extensions=((1, 2),),
        transport_kind=TransportKind.FLUID_PIPE,
    )
    rows = miner_cell_dicts_from_confirmed((_confirmed(c),), {c.candidate_id: c})
    kinds = [r["cell_kind"] for r in rows]
    assert "fluid_miner" in kinds
    assert "fluid_miner_extension" in kinds


def test_miner_missing_candidate_skipped() -> None:
    c = _gene_candidate(candidate_id="x", extractor=(0, 0))
    rows = miner_cell_dicts_from_confirmed((_confirmed(c),), {})  # empty candidates_by_id
    assert rows == ()


def test_miner_multiple_confirmed_produces_all_extractors() -> None:
    c1 = _gene_candidate(candidate_id="p1", extractor=(0, 0))
    c2 = _gene_candidate(candidate_id="p2", extractor=(5, 5))
    rows = miner_cell_dicts_from_confirmed(
        (_confirmed(c1), _confirmed(c2)),
        {c1.candidate_id: c1, c2.candidate_id: c2},
    )
    coords = [(r["server_x"], r["server_y"]) for r in rows]
    assert (0, 0) in coords
    assert (5, 5) in coords


def test_miner_cell_dicts_no_route_materialized_sentinel() -> None:
    c = _gene_candidate(candidate_id="e", extractor=(3, 3), extensions=((4, 3),))
    rows = miner_cell_dicts_from_confirmed((_confirmed(c),), {c.candidate_id: c})
    for row in rows:
        assert row["cell_kind"] != "route_materialized"


# ---------------------------------------------------------------------------
# full_cell_dicts_from_final_replay_state
# ---------------------------------------------------------------------------


def _loaded_snapshot_1x1(server_x: int = 0, server_y: int = 0) -> LoadedReconstructionSnapshot:
    cell = DecodedCellDTO(
        x=1,
        y=0,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind="shape_miner_extension",
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
        server_x=server_x,
        server_y=server_y,
    )
    return LoadedReconstructionSnapshot(cells=(cell,), server_xy_params=(1, 0))


def test_full_cell_dicts_includes_reconstruction_cells() -> None:
    loaded = _loaded_snapshot_1x1(server_x=0, server_y=0)
    mat = RouteMaterializationResult(layout=None, failure_reason=None)
    rows = full_cell_dicts_from_final_replay_state(loaded, mat, ())
    coords = {(r["server_x"], r["server_y"]) for r in rows}
    assert (0, 0) in coords


def test_full_cell_dicts_includes_transport_cells() -> None:
    loaded = _loaded_snapshot_1x1(server_x=0, server_y=0)
    mat = _mat_result(_mat_cell((2, 0), TransportKind.SHAPE_BELT))
    rows = full_cell_dicts_from_final_replay_state(loaded, mat, ())
    coords = {(r["server_x"], r["server_y"]) for r in rows}
    assert (2, 0) in coords


def test_full_cell_dicts_includes_miner_cells() -> None:
    loaded = _loaded_snapshot_1x1(server_x=0, server_y=0)
    mat = RouteMaterializationResult(layout=None, failure_reason=None)
    c = _gene_candidate(candidate_id="m1", extractor=(1, 1))
    rows = full_cell_dicts_from_final_replay_state(
        loaded, mat, (_confirmed(c),), candidates_by_id={c.candidate_id: c}
    )
    coords = {(r["server_x"], r["server_y"]) for r in rows}
    assert (1, 1) in coords


def test_full_cell_dicts_has_server_xy_keys() -> None:
    loaded = _loaded_snapshot_1x1()
    mat = RouteMaterializationResult(layout=None, failure_reason=None)
    rows = full_cell_dicts_from_final_replay_state(loaded, mat, ())
    assert rows
    for row in rows:
        assert "server_x" in row
        assert "server_y" in row


def test_result_layout_matches_materialized_plus_miners() -> None:
    """full_cell_dicts combines base + transport + miner without duplicates across types."""
    loaded = _loaded_snapshot_1x1(server_x=0, server_y=0)
    transport_cell = _mat_cell((3, 0), TransportKind.SHAPE_BELT)
    mat = _mat_result(transport_cell)
    miner = _gene_candidate(candidate_id="q1", extractor=(2, 0))
    rows = full_cell_dicts_from_final_replay_state(
        loaded, mat, (_confirmed(miner),), candidates_by_id={miner.candidate_id: miner}
    )
    coords = {(r["server_x"], r["server_y"]) for r in rows}
    assert (0, 0) in coords  # reconstruction base cell
    assert (3, 0) in coords  # transport belt cell
    assert (2, 0) in coords  # miner extractor cell
