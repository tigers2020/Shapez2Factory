"""Unit tests for simplified reconstruction: miner/extension → asteroid field."""

from __future__ import annotations

from pathlib import Path

from django_apps.asteroid_lab.reconstruction.perimeter_closing import close_diagonal_leaks
from django_apps.asteroid_lab.reconstruction.pipeline import reconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.shell import infer_shell_barrier_coords
from django_apps.asteroid_lab.reconstruction.topology_contract import decode_shapez_copy_string
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO


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


def test_miner_and_extension_become_synthetic_fields() -> None:
    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    by_xy = {(c.x, c.y): c for c in res.cells}
    assert by_xy[(1, 0)].cell_kind == "asteroid_fluid_field"
    assert by_xy[(3, 0)].cell_kind == "asteroid_fluid_field"
    assert (2, 0) not in by_xy
    assert res.summary_json["reconstruction_mode"] == "miner_extension_to_field"
    assert int(res.summary_json["synthetic_field_count"]) == 2


def test_interior_hole_is_not_filled() -> None:
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
    assert not any(c.x == 2 and c.y == 2 for c in res.cells)
    assert int(res.summary_json["filled_hole_cell_count"]) == 0


def test_unknown_ring_stays_unknown() -> None:
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
    by_xy = {(c.x, c.y): c for c in res.cells}
    for xy in ((1, 1), (2, 1), (3, 1), (1, 2), (3, 2), (1, 3), (2, 3), (3, 3)):
        assert by_xy[xy].cell_kind == "unknown"


def test_existing_asteroid_field_evidence_is_used_for_island_vote() -> None:
    minority = _cell(2, 1, cell_kind="asteroid_fluid_field", tile_type="KeepMe")
    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, cell_kind="asteroid_shape_field"),
        minority,
        _cell(3, 1, cell_kind="asteroid_shape_field"),
        _cell(1, 2, cell_kind="asteroid_shape_field"),
        _cell(3, 2, cell_kind="asteroid_shape_field"),
        _cell(1, 3, cell_kind="asteroid_shape_field"),
        _cell(2, 3, cell_kind="asteroid_shape_field"),
        _cell(3, 3, cell_kind="asteroid_shape_field"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    kept = next(c for c in res.cells if c.x == 2 and c.y == 1)
    assert kept.tile_type == "KeepMe"
    assert kept.cell_kind == "asteroid_fluid_field"


def test_reconstructed_non_transport_island_has_uniform_field_kind() -> None:
    """Each connected field component gets one kind; conflicting neighbors stay separate."""

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, cell_kind="asteroid_fluid_field"),
        _cell(2, 1, cell_kind="asteroid_shape_field"),
        _cell(3, 1, cell_kind="asteroid_fluid_field"),
        _cell(1, 2, cell_kind="asteroid_fluid_field"),
        _cell(3, 2, cell_kind="asteroid_fluid_field"),
        _cell(1, 3, cell_kind="asteroid_fluid_field"),
        _cell(2, 3, cell_kind="asteroid_fluid_field"),
        _cell(3, 3, cell_kind="asteroid_fluid_field"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    mid = next(c for c in res.cells if c.x == 2 and c.y == 1)
    assert mid.cell_kind == "asteroid_shape_field"
    fluid_ring = next(c for c in res.cells if c.x == 1 and c.y == 1)
    assert fluid_ring.cell_kind == "asteroid_fluid_field"


def test_shape_miner_becomes_shape_field() -> None:
    cells = (
        _cell(1, 0, cell_kind="shape_miner"),
        _cell(2, 0, cell_kind="space_belt", transport_kind="shape_belt"),
        _cell(3, 0, cell_kind="shape_miner_extension", transport_kind="shape_belt"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    kinds = {(c.x, c.y): c.cell_kind for c in res.cells}
    assert kinds[(1, 0)] == "asteroid_shape_field"
    assert kinds[(3, 0)] == "asteroid_shape_field"


def test_trace_collector_does_not_change_reconstruction_cells() -> None:
    from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
    from django_apps.asteroid_lab.reconstruction.pipeline import reconstruct_after_cleanup
    from django_apps.asteroid_lab.reconstruction.trace import ReconstructionTraceCollector

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
    )
    snap = _snapshot(cells)
    c = deconstruct_snapshot(snap)
    without = reconstruct_after_cleanup(
        cleaned_cells=c.cleaned_cells,
        original_cells=c.original_cells,
        removed_building_cells=c.removed_building_cells,
        wall_coords=c.wall_coords,
        bbox_bounds=c.bbox_bounds,
    )
    coll = ReconstructionTraceCollector()
    with_trace = reconstruct_after_cleanup(
        cleaned_cells=c.cleaned_cells,
        original_cells=c.original_cells,
        removed_building_cells=c.removed_building_cells,
        wall_coords=c.wall_coords,
        bbox_bounds=c.bbox_bounds,
        trace_collector=coll,
    )
    assert without.cells == with_trace.cells
    assert len(coll.events) == 1
    assert coll.events[0].trace_event_type == "reconstruction_final"


def test_original_map_all_extensions_become_fields() -> None:
    code = (
        Path(__file__).resolve().parents[3]
        / "documents"
        / "testmap"
        / "original_map.txt"
    ).read_text(encoding="utf-8").strip()
    snap = decode_shapez_copy_string(code)
    res = reconstruct_snapshot(snap)
    assert len(res.cells) == 578
    assert all(c.cell_kind == "asteroid_shape_field" for c in res.cells)
    assert int(res.summary_json["synthetic_field_count"]) == 578


def test_infer_shell_skips_strict_bbox_interior() -> None:
    walls = {(1, 1), (3, 1), (1, 3), (3, 3), (1, 2), (3, 2)}
    bbox = (-1, 3, 0, 4)
    inf = infer_shell_barrier_coords(walls, bbox)
    assert (2, 2) not in inf
    assert (2, 1) in inf or (2, 3) in inf


def test_close_diagonal_leaks_skips_strict_bbox_interior() -> None:
    bbox = (0, 4, 0, 4)
    solid = {(1, 1), (3, 3)}
    extra = close_diagonal_leaks(solid, bbox)
    assert (2, 2) not in extra


def test_close_diagonal_leaks_seals_three_corner_2x2_block() -> None:
    bbox = (0, 4, 0, 4)
    solid = {(1, 1), (2, 1), (1, 2)}
    extra = close_diagonal_leaks(solid, bbox)
    assert (2, 2) in extra
