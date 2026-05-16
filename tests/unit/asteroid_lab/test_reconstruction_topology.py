"""Unit tests for ``django_apps.asteroid_lab.reconstruction`` topology fill."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.pipeline import reconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.shell import infer_shell_barrier_coords
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


def test_interior_hole_filled_as_field_not_void() -> None:
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
    kinds = {c.cell_kind for c in res.cells}
    assert "internal_void" not in kinds
    hole = next(c for c in res.cells if c.x == 2 and c.y == 2)
    assert hole.cell_kind == "asteroid_shape_field"
    s = res.summary_json
    assert s.get("inferred_shell_cell_count", 0) >= 1
    assert int(s["barrier_cell_count"]) >= int(s["wall_cell_count"])
    assert int(s["filled_component_count"]) >= 1
    assert int(s["filled_hole_cell_count"]) == 1


def test_fluid_miner_inside_shell_fill_kind_not_from_miner_type() -> None:
    """Topology fill uses evidence field kinds, not removed miner fluid/shape."""

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, tile_type="UnknownTile_A"),
        _cell(2, 1, cell_kind="asteroid_shape_field", tile_type="RockShape"),
        _cell(3, 1, tile_type="UnknownTile_C"),
        _cell(1, 2, tile_type="UnknownTile_D"),
        _cell(3, 2, tile_type="UnknownTile_E"),
        _cell(1, 3, tile_type="UnknownTile_F"),
        _cell(2, 3, cell_kind="asteroid_shape_field", tile_type="RockShape2"),
        _cell(3, 3, tile_type="UnknownTile_H"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    hole = next(c for c in res.cells if c.x == 2 and c.y == 2)
    assert hole.cell_kind == "asteroid_shape_field"


def test_incomplete_shell_does_not_overfill() -> None:
    """Single wall row: cavity touches bbox / fails two-axis guard → no fill."""

    cells = (
        _cell(1, 0, tile_type="UnknownTile_R1"),
        _cell(2, 0, tile_type="UnknownTile_R2"),
        _cell(3, 0, tile_type="UnknownTile_R3"),
        _cell(1, 1, cell_kind="fluid_miner"),
        _cell(2, 1, cell_kind="fluid_miner"),
        _cell(3, 1, cell_kind="fluid_miner"),
        _cell(1, 2, cell_kind="fluid_miner"),
        _cell(2, 2, cell_kind="fluid_miner"),
        _cell(3, 2, cell_kind="fluid_miner"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    assert not any(c.x == 2 and c.y == 2 for c in res.cells)
    s = res.summary_json
    assert int(s["filled_hole_cell_count"]) == 0
    assert int(s["filled_component_count"]) == 0


def test_infer_shell_skips_strict_bbox_interior() -> None:
    """Do not infer barrier across the hole inside the tight wall bbox (row span)."""

    walls = {(1, 1), (3, 1), (1, 3), (3, 3), (1, 2), (3, 2)}
    bbox = (-1, 3, 0, 4)
    inf = infer_shell_barrier_coords(walls, bbox)
    assert (2, 2) not in inf
    assert (2, 1) in inf or (2, 3) in inf


def test_existing_asteroid_field_evidence_not_overwritten() -> None:
    corner = _cell(2, 1, cell_kind="asteroid_fluid_field", tile_type="KeepMe")
    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, tile_type="UnknownTile_A"),
        corner,
        _cell(3, 1, tile_type="UnknownTile_C"),
        _cell(1, 2, tile_type="UnknownTile_D"),
        _cell(3, 2, tile_type="UnknownTile_E"),
        _cell(1, 3, tile_type="UnknownTile_F"),
        _cell(2, 3, tile_type="UnknownTile_G"),
        _cell(3, 3, tile_type="UnknownTile_H"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    kept = next(c for c in res.cells if c.x == 2 and c.y == 1)
    assert kept.tile_type == "KeepMe"
    assert kept.cell_kind == "asteroid_fluid_field"


def test_deterministic_tie_break_prefers_shape() -> None:
    """Equal fluid/shape evidence counts → ``asteroid_shape_field``."""

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, cell_kind="asteroid_fluid_field"),
        _cell(2, 1, cell_kind="asteroid_shape_field"),
        _cell(3, 1, cell_kind="asteroid_fluid_field"),
        _cell(1, 2, cell_kind="asteroid_shape_field"),
        _cell(3, 2, cell_kind="asteroid_fluid_field"),
        _cell(1, 3, cell_kind="asteroid_shape_field"),
        _cell(2, 3, cell_kind="asteroid_fluid_field"),
        _cell(3, 3, cell_kind="asteroid_shape_field"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    hole = next(c for c in res.cells if c.x == 2 and c.y == 2)
    assert hole.cell_kind == "asteroid_shape_field"


def test_trace_collector_does_not_change_reconstruction_cells() -> None:
    from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
    from django_apps.asteroid_lab.reconstruction.pipeline import reconstruct_after_cleanup
    from django_apps.asteroid_lab.reconstruction.trace import ReconstructionTraceCollector

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
    c = deconstruct_snapshot(snap)
    without = reconstruct_after_cleanup(
        cleaned_cells=c.cleaned_cells,
        wall_coords=c.wall_coords,
        bbox_bounds=c.bbox_bounds,
        server_xy_params=c.server_xy_params,
    )
    coll = ReconstructionTraceCollector()
    with_trace = reconstruct_after_cleanup(
        cleaned_cells=c.cleaned_cells,
        wall_coords=c.wall_coords,
        bbox_bounds=c.bbox_bounds,
        server_xy_params=c.server_xy_params,
        trace_collector=coll,
    )
    assert without.cells == with_trace.cells
    assert len(coll.events) >= 2
    finals = [e for e in coll.events if e.trace_event_type == "reconstruction_final"]
    assert len(finals) == 1
    keys = [str(e.summary_json.get("event_key", "")) for e in coll.events]
    assert "step4_09_reconstruction_final" in keys
