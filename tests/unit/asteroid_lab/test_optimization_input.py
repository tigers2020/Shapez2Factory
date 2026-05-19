"""Optimization input contracts (Sequence 1A/1B, Solver Runtime PR1B)."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab.optimization.coords import cardinal_unit_toward, neighbors4_server
from django_apps.asteroid_lab.optimization.enums import Direction, TransportKind, TransportMask
from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.loaded_snapshot import (
    LoadedReconstructionSnapshot,
    loaded_reconstruction_snapshot_from_result,
)
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    mineable_field_kind,
    optimization_input_from_loaded_snapshot,
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.route_domain import RouteDomainSnapshotBuilder
from django_apps.asteroid_lab.reconstruction.pipeline import reconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO
from django_apps.asteroid_lab.snapshots.server_coords import server_xy_for_raw_xy

_OPTIMIZATION_PKG = (
    Path(__file__).resolve().parents[3] / "django_apps" / "asteroid_lab" / "optimization"
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


def _hole_fixture_cells() -> tuple[DecodedCellDTO, ...]:
    return (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, tile_type="UnknownTile_A"),
        _cell(2, 1, cell_kind="fluid_miner"),
        _cell(3, 1, tile_type="UnknownTile_C"),
        _cell(1, 2, tile_type="UnknownTile_D"),
        _cell(3, 2, tile_type="UnknownTile_E"),
        _cell(1, 3, tile_type="UnknownTile_F"),
        _cell(2, 3, tile_type="UnknownTile_G"),
        _cell(3, 3, tile_type="UnknownTile_H"),
    )


def _hole_reconstruction() -> ReconstructionResult:
    return reconstruct_snapshot(_snapshot(_hole_fixture_cells()))


def _server_coord(c: DecodedCellDTO, res: ReconstructionResult) -> tuple[int, int]:
    if c.server_x is not None and c.server_y is not None:
        return (c.server_x, c.server_y)
    p = res.server_xy_params
    assert p is not None
    return server_xy_for_raw_xy(c.x, c.y, min_dense_x=p[0], min_raw_y=p[1])


def test_neighbors4_server_includes_x_zero_neighbor() -> None:
    c = (0, 5)
    n = neighbors4_server(c)
    assert (-1, 5) in n
    assert (1, 5) in n
    assert (0, 4) in n
    assert (0, 6) in n
    assert len(n) == 4


def test_cardinal_unit_toward_diagonal_raises() -> None:
    with pytest.raises(ValueError, match="Manhattan"):
        cardinal_unit_toward((0, 0), (1, 1))


def test_cardinal_unit_toward_east() -> None:
    assert cardinal_unit_toward((0, 0), (3, 0)) == Direction.E


def test_greenfield_optimization_input_contract() -> None:
    inp = greenfield_optimization_input()
    assert inp.existing_transport_cells == frozenset()
    assert inp.existing_trunk_cells == frozenset()
    assert inp.protected_corridor_cells == frozenset()
    assert inp.existing_trunk_cells <= {c.coord for c in inp.existing_transport_cells}


def test_optimization_input_greenfield_is_empty_transport_and_trunk_and_protected() -> None:
    inp = greenfield_optimization_input(bbox=BBox(0, 2, 0, 2))
    assert inp.existing_transport_cells == frozenset()
    assert inp.existing_trunk_cells == frozenset()
    assert inp.protected_corridor_cells == frozenset()


def test_optimization_input_topology_graph_adjacency_matches_neighbors4_server() -> None:
    res = _hole_reconstruction()
    inp = optimization_input_from_reconstruction(res)
    graph = inp.topology_graph
    adj: dict[tuple[int, int], set[tuple[int, int]]] = {}
    for e in graph.edges:
        adj.setdefault(e.a, set()).add(e.b)

    by_server: dict[tuple[int, int], DecodedCellDTO] = {}
    for c in res.cells:
        by_server[_server_coord(c, res)] = c

    for sv, cell in by_server.items():
        if cell.cell_kind not in ("asteroid_shape_field", "asteroid_fluid_field"):
            continue
        expected = {n for n in neighbors4_server(sv) if n in by_server}
        assert adj.get(sv, set()) == expected


def test_optimization_input_preserves_inferred_fill_as_mineable() -> None:
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
    res = reconstruct_snapshot(_snapshot(cells))
    inp = optimization_input_from_reconstruction(res)
    hole = next(c for c in res.cells if c.x == 2 and c.y == 2)
    assert hole.cell_kind in ("asteroid_shape_field", "asteroid_fluid_field")
    assert _server_coord(hole, res) in inp.mineable_cells


def test_optimization_input_marks_rim_cells() -> None:
    res = _hole_reconstruction()
    inp = optimization_input_from_reconstruction(res)
    assert inp.rim_cells & inp.interior_cells == frozenset()
    assert inp.rim_cells | inp.interior_cells == inp.mineable_cells
    for sv in inp.rim_cells:
        nbs = neighbors4_server(sv)
        assert any(n not in inp.mineable_cells for n in nbs)


def test_optimization_input_transport_removed_not_asteroid_evidence() -> None:
    res = _hole_reconstruction()
    inp = optimization_input_from_reconstruction(res)
    for c in res.cells:
        if c.cell_kind == "space_pipe":
            sv = _server_coord(c, res)
            assert sv not in inp.mineable_cells
            assert sv not in inp.asteroid_cells


def test_optimization_input_existing_transport_unique_coord() -> None:
    res = _hole_reconstruction()
    inp = optimization_input_from_reconstruction(res)
    coords = [t.coord for t in inp.existing_transport_cells]
    assert len(coords) == len(set(coords))


def test_optimization_input_existing_transport_sets_transport_mask_inputs() -> None:
    res = _hole_reconstruction()
    inp = optimization_input_from_reconstruction(res)
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    for tc in inp.existing_transport_cells:
        cell = domain[tc.coord]
        assert cell.route_class.value == "transport"
        if tc.transport_kind == TransportKind.FLUID_PIPE:
            assert cell.transport_mask == TransportMask.FLUID_PIPE
        elif tc.transport_kind == TransportKind.SHAPE_BELT:
            assert cell.transport_mask == TransportMask.SHAPE_BELT


def test_optimization_input_trunk_cells_subset_of_transport_cells() -> None:
    res = _hole_reconstruction()
    inp = optimization_input_from_reconstruction(res)
    transport_coords = {c.coord for c in inp.existing_transport_cells}
    assert inp.existing_trunk_cells <= transport_coords


def test_optimization_input_route_goals_touch_external_void_or_trunk_contract() -> None:
    """Phase B: route_goals are empty/seed only — planned goals are Phase C."""

    res = _hole_reconstruction()
    inp = optimization_input_from_reconstruction(res)
    assert inp.route_goals == frozenset()


def test_optimization_input_adapter_normalizes_extension_kind_to_mineable() -> None:
    """§0.3: extension anchor kind is normalized at adapter without mutating cell."""

    ext = _cell(4, 0, cell_kind="fluid_miner_extension", server_x=4, server_y=0)
    snap = LoadedReconstructionSnapshot(
        cells=(ext,),
        server_xy_params=None,
    )
    assert ext.cell_kind == "fluid_miner_extension"
    assert mineable_field_kind(ext) == "asteroid_fluid_field"
    inp = optimization_input_from_loaded_snapshot(snap)
    assert (4, 0) in inp.mineable_cells


def test_loaded_reconstruction_snapshot_from_result_preserves_cells() -> None:
    res = _hole_reconstruction()
    loaded = loaded_reconstruction_snapshot_from_result(res)
    assert loaded.cells == res.cells
    inp1 = optimization_input_from_reconstruction(res)
    inp2 = optimization_input_from_loaded_snapshot(loaded)
    assert inp1 == inp2


def test_optimization_package_has_no_legacy_camelcase_extension_kind_strings() -> None:
    forbidden = ("shapeMinerExtension", "fluidMinerExtension", "Layout_ShapeMinerExtension")
    for py in _OPTIMIZATION_PKG.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{token} found in {py.name}"


def test_seed_route_domain_blocked_matches_optimization_input() -> None:
    res = _hole_reconstruction()
    inp = optimization_input_from_reconstruction(res)
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    for c in inp.blocked_cells:
        assert domain[c].hard_blocked is True

    mine_sv = next(iter(inp.mineable_cells))
    mcell = domain[mine_sv]
    assert mcell.hard_blocked is False
    assert mcell.transport_mask == TransportMask.BOTH
