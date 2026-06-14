"""Regression: simplified reconstruction does not invent fill beyond miner/extension coords."""

from __future__ import annotations

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.evidence import is_asteroid_evidence
from django_apps.asteroid_lab.reconstruction.grid import Coord
from django_apps.asteroid_lab.reconstruction.pipeline import (
    reconstruct_snapshot,
    run_topology_reconstruction,
)
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO
from django_apps.asteroid_lab.snapshots.transport_components import is_transport_tile

_FIELD_KINDS = frozenset({"asteroid_shape_field", "asteroid_fluid_field"})


def _cell(
    x: int,
    y: int,
    *,
    tile_type: str = "",
    cell_kind: str = "unknown",
    transport_kind: str = "none",
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


def _filled_field_coords(res_cells: tuple[DecodedCellDTO, ...]) -> set[Coord]:
    return {(c.x, c.y) for c in res_cells if c.cell_kind in _FIELD_KINDS}


def _hole_island_cells() -> tuple[DecodedCellDTO, ...]:
    return (
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


def test_reconstruction_does_not_fill_interior_hole() -> None:
    res = reconstruct_snapshot(_snapshot(_hole_island_cells()))
    assert (2, 2) not in _filled_field_coords(res.cells)
    assert int(res.summary_json["filled_hole_cell_count"]) == 0


def test_reconstruction_only_fields_at_miner_extension_coords() -> None:
    res = reconstruct_snapshot(_snapshot(_hole_island_cells()))
    filled = _filled_field_coords(res.cells)
    assert filled == {(1, 0), (3, 0)}


def test_reconstruction_summary_mode() -> None:
    cleanup = deconstruct_snapshot(_snapshot(_hole_island_cells()))
    res = run_topology_reconstruction(cleanup)
    assert res.summary_json["reconstruction_mode"] == "miner_extension_to_field"


def test_reconstruction_belt_pipe_not_evidence() -> None:
    cells = (
        _cell(1, 2, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 2, cell_kind="space_pipe", transport_kind="fluid_pipe"),
    )
    cleanup = deconstruct_snapshot(_snapshot(cells))
    assert (1, 2) not in cleanup.wall_coords
    assert (3, 2) not in cleanup.wall_coords
    assert not is_asteroid_evidence(cells[0])
    assert is_transport_tile(cells[0])


def test_reconstruction_miner_extension_become_fields_only() -> None:
    cells = (
        _cell(1, 2, cell_kind="fluid_miner"),
        _cell(3, 2, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    filled = _filled_field_coords(res.cells)
    assert filled == {(1, 2), (3, 2)}
    assert (2, 2) not in filled
