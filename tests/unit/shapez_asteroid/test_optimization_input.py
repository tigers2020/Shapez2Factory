"""Sequence 1A/1B: optimization input contracts and reconstruction adapter."""

from __future__ import annotations

import importlib

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.pipeline import (
    reconstruct_snapshot,
    run_topology_reconstruction,
)
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO
from django_apps.shapez_asteroid.adapters.reconstruction_adapter import (
    build_optimization_input,
    decoded_cell_to_server_coord,
)
from django_apps.shapez_asteroid.optimization.coords import Coord, neighbors4_server
from django_apps.shapez_asteroid.optimization.dto import (
    ExistingTransportCell,
    RouteGoal,
    TopologyEdge,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CandidateRejectReason,
    CommitConflictReason,
    EvolutionConvergenceReason,
    OptimizationReplayEventType,
    RouteGoalKind,
    RouteProbeFailureReason,
    TransportKind,
    ValidationIssueCode,
    ValidationSeverity,
)


def _cell(
    x: int,
    y: int,
    *,
    tile_type: str = "",
    cell_kind: str = "unknown",
    transport_kind: str = "none",
    server_x: int | None = None,
    server_y: int | None = None,
) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type=tile_type,
        cell_kind=cell_kind,
        transport_kind=transport_kind,
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
        server_x=server_x,
        server_y=server_y,
    )


def _snapshot(cells: tuple[DecodedCellDTO, ...]) -> DecodedBlueprintSnapshotDTO:
    xs = [c.x for c in cells]
    ys = [c.y for c in cells]
    mn_x, mx_x = min(xs), max(xs)
    mn_y, mx_y = min(ys), max(ys)
    ck: dict[str, int] = {}
    for c in cells:
        ck[c.cell_kind] = ck.get(c.cell_kind, 0) + 1
    return DecodedBlueprintSnapshotDTO(
        project_id=None,
        map_input_id=None,
        binary_version=3,
        blueprint_type="Island",
        entry_count=len(cells),
        bbox_json={
            "min_x": mn_x,
            "max_x": mx_x,
            "min_y": mn_y,
            "max_y": mx_y,
            "width": mx_x - mn_x + 1,
            "height": mx_y - mn_y + 1,
        },
        cell_kind_counts_json=ck,
        transport_kind_counts_json={},
        cells=cells,
        summary_json={},
    )


def test_imports_no_cycles() -> None:
    o = importlib.import_module("django_apps.shapez_asteroid.optimization")
    a = importlib.import_module("django_apps.shapez_asteroid.adapters.reconstruction_adapter")
    assert o.Coord is not None
    assert a.build_optimization_input is not None


def test_enum_values_match_phase_docs() -> None:
    assert RouteProbeFailureReason.NO_GOAL_CELLS.value == "no_goal_cells"
    assert CandidateRejectReason.ROUTE_PROBE_UNREACHABLE.value == "route_probe_unreachable"
    assert ValidationSeverity.ERROR.value == "error"
    assert ValidationIssueCode.ORPHAN_TRANSPORT.value == "orphan_transport"
    assert ValidationIssueCode.CANDIDATE_POOL_MISSING.value == "candidate_pool_missing"
    assert EvolutionConvergenceReason.MAX_STALL_GENERATION.value == "max_stall_generation"
    assert CommitConflictReason.TRUNK_DEADLOCK.value == "trunk_deadlock"
    assert OptimizationReplayEventType.ROUTE_PROBE_FAILED.value == "route_probe.failed"


def test_neighbors4_server_includes_x0_dense_adjacency() -> None:
    c = Coord(0, 2)
    n = neighbors4_server(c)
    assert Coord(-1, 2) in n
    assert Coord(1, 2) in n
    assert Coord(0, 1) in n
    assert Coord(0, 3) in n
    assert len(n) == 4


def test_topology_graph_edges_match_neighbors4_server() -> None:
    cells = (
        _cell(1, 1, cell_kind="asteroid_shape_field", server_x=0, server_y=0),
        _cell(2, 1, cell_kind="asteroid_shape_field", server_x=1, server_y=0),
    )
    snap = _snapshot(cells)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    inp = build_optimization_input(recon, cleanup)
    for e in inp.topology_graph.edges:
        assert isinstance(e, TopologyEdge)
        assert e.b in neighbors4_server(e.a)


def test_route_goal_priority_lower_is_more_preferred() -> None:
    g0 = RouteGoal(
        Coord(0, 0),
        RouteGoalKind.TRUNK_SEED,
        TransportKind.SHAPE_BELT,
        priority=0,
        existing_trunk=True,
    )
    g1 = RouteGoal(
        Coord(1, 0),
        RouteGoalKind.EXTERNAL_MARGIN,
        None,
        priority=20,
        existing_trunk=False,
    )
    assert g0.priority < g1.priority


def test_greenfield_empty_transport_trunk_protected() -> None:
    cells = (
        _cell(1, 1, cell_kind="asteroid_shape_field", server_x=0, server_y=0),
        _cell(2, 1, cell_kind="asteroid_shape_field", server_x=1, server_y=0),
        _cell(1, 2, cell_kind="asteroid_shape_field", server_x=0, server_y=1),
        _cell(2, 2, cell_kind="asteroid_shape_field", server_x=1, server_y=1),
    )
    snap = _snapshot(cells)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    inp = build_optimization_input(recon, cleanup)
    assert inp.existing_transport_cells == frozenset()
    assert inp.existing_trunk_cells == frozenset()
    assert inp.protected_corridor_cells == frozenset()


def test_existing_trunk_subset_of_transport_coords() -> None:
    cells = (
        _cell(1, 0, cell_kind="space_belt", transport_kind="shape_belt", server_x=0, server_y=0),
        _cell(1, 1, cell_kind="asteroid_shape_field", server_x=0, server_y=1),
    )
    snap = _snapshot(cells)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    trunk_bad = frozenset({Coord(5, 5)})
    et = frozenset({ExistingTransportCell(Coord(0, 0), TransportKind.SHAPE_BELT)})
    inp = build_optimization_input(
        recon, cleanup, existing_transport_cells=et, existing_trunk_cells=trunk_bad
    )
    assert inp.existing_trunk_cells == frozenset()
    trunk_ok = frozenset({Coord(0, 0)})
    inp2 = build_optimization_input(
        recon, cleanup, existing_transport_cells=et, existing_trunk_cells=trunk_ok
    )
    assert inp2.existing_trunk_cells == frozenset({Coord(0, 0)})


def test_hole_interior_stays_mineable() -> None:
    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, tile_type="UnknownTile_A"),
        _cell(2, 1, tile_type="UnknownTile_B"),
        _cell(3, 1, tile_type="UnknownTile_C"),
        _cell(1, 2, tile_type="UnknownTile_D"),
        _cell(3, 2, tile_type="UnknownTile_E"),
        _cell(1, 3, tile_type="UnknownTile_F"),
        _cell(2, 3, tile_type="UnknownTile_G"),
        _cell(3, 3, tile_type="UnknownTile_H"),
    )
    recon = reconstruct_snapshot(_snapshot(cells))
    cleanup = deconstruct_snapshot(_snapshot(cells))
    inp = build_optimization_input(recon, cleanup)
    hole_cell = next(c for c in recon.cells if c.x == 2 and c.y == 2)
    hole = decoded_cell_to_server_coord(hole_cell, server_xy_params=cleanup.server_xy_params)
    assert hole in inp.mineable_cells
    assert hole in inp.asteroid_cells


def test_belt_removed_coord_not_asteroid_evidence_default() -> None:
    """Pipe-only removal site must not be classified as asteroid field in OptimizationInput."""

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, tile_type="UnknownTile_A"),
        _cell(2, 1, tile_type="UnknownTile_B"),
        _cell(3, 1, tile_type="UnknownTile_C"),
        _cell(1, 2, tile_type="UnknownTile_D"),
        _cell(3, 2, tile_type="UnknownTile_E"),
        _cell(1, 3, tile_type="UnknownTile_F"),
        _cell(2, 3, tile_type="UnknownTile_G"),
        _cell(3, 3, tile_type="UnknownTile_H"),
    )
    snap = _snapshot(cells)
    cleanup = deconstruct_snapshot(snap)
    recon = reconstruct_snapshot(snap)
    inp = build_optimization_input(recon, cleanup)
    pipe_xy = decoded_cell_to_server_coord(
        next(c for c in cleanup.ignored_transport_cells if c.cell_kind == "space_pipe"),
        server_xy_params=cleanup.server_xy_params,
    )
    assert pipe_xy not in inp.asteroid_cells


def test_extractor_removed_anchor_supports_mineable_hole() -> None:
    """Removed miner/extension contributes to reconstruction fill (hole stays mineable)."""

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, tile_type="UnknownTile_A"),
        _cell(2, 1, tile_type="UnknownTile_B"),
        _cell(3, 1, tile_type="UnknownTile_C"),
        _cell(1, 2, tile_type="UnknownTile_D"),
        _cell(3, 2, tile_type="UnknownTile_E"),
        _cell(1, 3, tile_type="UnknownTile_F"),
        _cell(2, 3, tile_type="UnknownTile_G"),
        _cell(3, 3, tile_type="UnknownTile_H"),
    )
    snap = _snapshot(cells)
    cleanup = deconstruct_snapshot(snap)
    recon = reconstruct_snapshot(snap)
    inp = build_optimization_input(recon, cleanup)
    assert inp.mineable_cells


def test_all_optimization_input_coords_are_server_xy() -> None:
    cells = (
        _cell(10, 20, cell_kind="asteroid_shape_field", server_x=2, server_y=3),
        _cell(11, 20, cell_kind="space_belt", transport_kind="shape_belt", server_x=3, server_y=3),
    )
    snap = _snapshot(cells)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    inp = build_optimization_input(recon, cleanup)
    for c in inp.asteroid_cells | inp.mineable_cells | inp.rim_cells | inp.interior_cells:
        assert isinstance(c, Coord)
    for c in inp.external_void_cells | inp.blocked_cells | inp.protected_corridor_cells:
        assert isinstance(c, Coord)
    for e in inp.existing_transport_cells:
        assert isinstance(e.coord, Coord)
