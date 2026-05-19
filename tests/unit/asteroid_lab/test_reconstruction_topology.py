"""Unit tests for ``django_apps.asteroid_lab.reconstruction`` topology fill."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.perimeter_closing import close_diagonal_leaks
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
    """No decoded asteroid_*_field around the hole → island resolves to ``asteroid_shape_field``."""

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
    assert hole.cell_kind in ("asteroid_shape_field", "asteroid_fluid_field")
    s = res.summary_json
    assert int(s.get("inferred_shell_cell_count", 0)) == 0
    assert int(s["barrier_cell_count"]) >= int(s["wall_cell_count"])
    assert int(s["filled_component_count"]) >= 1
    assert int(s["filled_hole_cell_count"]) >= 1


def test_unknown_ring_not_stamped_on_hole_island() -> None:
    """UnknownTile ring stays ``unknown``; only the interior hole becomes ``asteroid_*_field``."""

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
    assert by_xy[(2, 2)].cell_kind in ("asteroid_shape_field", "asteroid_fluid_field")
    for xy in ((1, 1), (2, 1), (3, 1), (1, 2), (3, 2), (1, 3), (2, 3), (3, 3)):
        assert by_xy[xy].cell_kind == "unknown"


def test_topology_fill_uses_removed_fluid_miner_wall_as_field_evidence() -> None:
    """Stripped fluid miner neighbor still counts as ``asteroid_fluid_field`` evidence for fill."""

    cells = (
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
    res = reconstruct_snapshot(_snapshot(cells))
    hole = next(c for c in res.cells if c.x == 2 and c.y == 2)
    assert hole.cell_kind == "asteroid_fluid_field"


def test_fluid_miner_inside_shell_fill_kind_not_from_miner_type() -> None:
    """Miner equipment type is not fill evidence; dominant decoded shape field → shape fill."""

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


def test_existing_asteroid_field_evidence_is_used_for_island_vote() -> None:
    """Island majority from original evidence can replace a minority decoded ``cell_kind``."""

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
    assert kept.cell_kind == "asteroid_shape_field"


def test_reconstructed_non_transport_island_has_uniform_field_kind() -> None:
    """Island stamping overwrites a minority decoded field so the whole island matches."""

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
    hole = next(c for c in res.cells if c.x == 2 and c.y == 2)
    assert mid.cell_kind == "asteroid_fluid_field"
    assert hole.cell_kind == "asteroid_fluid_field"


def test_topology_fill_follows_fluid_field_majority_evidence() -> None:
    """Fluid ``asteroid_fluid_field`` majority on the island stamps the hole the same way."""

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, cell_kind="asteroid_fluid_field"),
        _cell(2, 1, cell_kind="asteroid_fluid_field"),
        _cell(3, 1, cell_kind="asteroid_fluid_field"),
        _cell(1, 2, cell_kind="asteroid_fluid_field"),
        _cell(3, 2, cell_kind="asteroid_fluid_field"),
        _cell(1, 3, cell_kind="asteroid_fluid_field"),
        _cell(2, 3, cell_kind="asteroid_fluid_field"),
        _cell(3, 3, cell_kind="asteroid_fluid_field"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    filled = next(c for c in res.cells if c.x == 2 and c.y == 2)
    assert filled.cell_kind == "asteroid_fluid_field"
    raw = filled.raw_entry_json
    assert isinstance(raw, dict)
    assert raw.get("_replay_synthetic") is True
    assert raw.get("_reconstruction") == "topology_fill"


def test_topology_fill_falls_back_to_shape_on_tie_or_no_evidence() -> None:
    """Equal fluid/shape field counts in the island vote → ``asteroid_shape_field`` fallback."""

    cells = (
        _cell(1, 0, cell_kind="shape_miner"),
        _cell(2, 0, cell_kind="space_belt", transport_kind="shape_belt"),
        _cell(3, 0, cell_kind="shape_miner_extension", transport_kind="shape_belt"),
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


def test_topology_fill_ignores_miner_type_when_field_evidence_disagrees() -> None:
    """Fill kind follows decoded field evidence around the hole, not miner row equipment."""

    cells_fluid_miner_shape_evidence = (
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
    res_shape = reconstruct_snapshot(_snapshot(cells_fluid_miner_shape_evidence))
    hole_shape = next(c for c in res_shape.cells if c.x == 2 and c.y == 2)
    assert hole_shape.cell_kind == "asteroid_shape_field"

    cells_shape_miner_fluid_evidence = (
        _cell(1, 0, cell_kind="shape_miner"),
        _cell(2, 0, cell_kind="space_belt", transport_kind="shape_belt"),
        _cell(3, 0, cell_kind="shape_miner_extension", transport_kind="shape_belt"),
        _cell(1, 1, cell_kind="asteroid_fluid_field"),
        _cell(2, 1, cell_kind="asteroid_fluid_field"),
        _cell(3, 1, cell_kind="asteroid_fluid_field"),
        _cell(1, 2, cell_kind="asteroid_fluid_field"),
        _cell(3, 2, cell_kind="asteroid_fluid_field"),
        _cell(1, 3, cell_kind="asteroid_fluid_field"),
        _cell(2, 3, cell_kind="asteroid_fluid_field"),
        _cell(3, 3, cell_kind="asteroid_fluid_field"),
    )
    res_fluid = reconstruct_snapshot(_snapshot(cells_shape_miner_fluid_evidence))
    hole_fluid = next(c for c in res_fluid.cells if c.x == 2 and c.y == 2)
    assert hole_fluid.cell_kind == "asteroid_fluid_field"


def test_island_stamp_preserves_existing_ring_and_topology_fill_xy() -> None:
    """Ring and hole fill cells survive; island uses one ``asteroid_*_field`` kind."""

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, cell_kind="asteroid_fluid_field"),
        _cell(2, 1, cell_kind="asteroid_fluid_field"),
        _cell(3, 1, cell_kind="asteroid_fluid_field"),
        _cell(1, 2, cell_kind="asteroid_fluid_field"),
        _cell(3, 2, cell_kind="asteroid_fluid_field"),
        _cell(1, 3, cell_kind="asteroid_fluid_field"),
        _cell(2, 3, cell_kind="asteroid_fluid_field"),
        _cell(3, 3, cell_kind="asteroid_fluid_field"),
    )
    original_ring_xy = {(c.x, c.y) for c in cells if c.cell_kind == "asteroid_fluid_field"}
    topology_fill_xy = {(2, 2)}
    res = reconstruct_snapshot(_snapshot(cells))
    out_xy = {(c.x, c.y) for c in res.cells}
    assert original_ring_xy <= out_xy
    assert topology_fill_xy <= out_xy
    kinds = {next(c for c in res.cells if (c.x, c.y) == xy).cell_kind for xy in original_ring_xy}
    kinds |= {next(c for c in res.cells if c.x == 2 and c.y == 2).cell_kind}
    assert kinds == {"asteroid_fluid_field"}


def test_reconstruction_cell_count_not_less_than_pre_stamp_merge() -> None:
    """Island stamp runs on cleaned ∪ fill; cell count never drops vs merged pre-stamp."""

    from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
    from django_apps.asteroid_lab.reconstruction.island import stamp_islands_uniform
    from django_apps.asteroid_lab.reconstruction.pipeline import reconstruct_after_cleanup
    from django_apps.asteroid_lab.snapshots.transport_components import sort_key_xy_layer

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, cell_kind="asteroid_fluid_field"),
        _cell(2, 1, cell_kind="asteroid_fluid_field"),
        _cell(3, 1, cell_kind="asteroid_fluid_field"),
        _cell(1, 2, cell_kind="asteroid_fluid_field"),
        _cell(3, 2, cell_kind="asteroid_fluid_field"),
        _cell(1, 3, cell_kind="asteroid_fluid_field"),
        _cell(2, 3, cell_kind="asteroid_fluid_field"),
        _cell(3, 3, cell_kind="asteroid_fluid_field"),
    )
    snap = _snapshot(cells)
    c = deconstruct_snapshot(snap)
    res = reconstruct_after_cleanup(
        cleaned_cells=c.cleaned_cells,
        original_cells=c.original_cells,
        removed_building_cells=c.removed_building_cells,
        wall_coords=c.wall_coords,
        bbox_bounds=c.bbox_bounds,
        server_xy_params=c.server_xy_params,
    )
    stripped_by_key = {(cell.x, cell.y, cell.layer): cell for cell in c.cleaned_cells}
    stripped_xy = {(x, y) for x, y, _ in stripped_by_key}
    filled_only = [cell for cell in res.cells if (cell.x, cell.y) not in stripped_xy]
    assert len(filled_only) >= 1
    merged_before_stamp: dict[tuple[int, int, int | None], object] = dict(stripped_by_key)
    for cell in filled_only:
        merged_before_stamp[(cell.x, cell.y, cell.layer)] = cell
    merged_tuple = tuple(sorted(merged_before_stamp.values(), key=sort_key_xy_layer))
    stamped = stamp_islands_uniform(
        merged_tuple,
        original_cells=c.original_cells,
        removed_building_cells=c.removed_building_cells,
    )
    assert len(stamped) == len(merged_tuple)
    assert {(c.x, c.y, c.layer) for c in stamped} == {(c.x, c.y, c.layer) for c in merged_tuple}
    assert len(res.cells) == len(merged_tuple)


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
        original_cells=c.original_cells,
        removed_building_cells=c.removed_building_cells,
        wall_coords=c.wall_coords,
        bbox_bounds=c.bbox_bounds,
        server_xy_params=c.server_xy_params,
    )
    coll = ReconstructionTraceCollector()
    with_trace = reconstruct_after_cleanup(
        cleaned_cells=c.cleaned_cells,
        original_cells=c.original_cells,
        removed_building_cells=c.removed_building_cells,
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


def test_reconstruction_fills_enclosed_internal_holes_as_mineable() -> None:
    """Concave ring: interior hole becomes ``asteroid_*_field``, not void."""

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
    assert "internal_void" not in {c.cell_kind for c in res.cells}
    hole = next(c for c in res.cells if c.x == 2 and c.y == 2)
    assert hole.cell_kind in ("asteroid_shape_field", "asteroid_fluid_field")


def test_reconstruction_does_not_mark_external_void_as_mineable() -> None:
    """Open cavity touching bbox padding is not filled as mineable field."""

    cells = (
        _cell(1, 0, tile_type="UnknownTile_R1"),
        _cell(2, 0, tile_type="UnknownTile_R2"),
        _cell(3, 0, tile_type="UnknownTile_R3"),
        _cell(1, 1, cell_kind="fluid_miner"),
        _cell(2, 1, cell_kind="fluid_miner"),
        _cell(3, 1, cell_kind="fluid_miner"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    assert not any(c.x == 2 and c.y == 2 for c in res.cells)
    assert int(res.summary_json.get("filled_hole_cell_count", 0)) == 0


def test_reconstruction_transport_removed_cells_are_not_asteroid_evidence() -> None:
    """Pipe-only anchors on a 1-cell row do not seal an interior slit."""

    cells = (
        _cell(1, 2, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 2, cell_kind="space_pipe", transport_kind="fluid_pipe"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    assert not any(c.x == 2 and c.y == 2 for c in res.cells)
    assert int(res.summary_json.get("sealed_slit_cell_count", 0)) == 0


def test_reconstruction_extractor_extension_cells_are_asteroid_evidence() -> None:
    """Stripped miner/extension anchors are walls; external 1-cell gap is not slit-filled."""

    cells = (
        _cell(1, 2, cell_kind="fluid_miner"),
        _cell(3, 2, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    assert not any(c.x == 2 and c.y == 2 for c in res.cells)
    assert int(res.summary_json.get("sealed_slit_cell_count", 0)) == 0
    assert int(res.summary_json.get("inferred_shell_cell_count", 0)) == 0


def test_reconstruction_chebyshev_closing_does_not_seal_strict_interior_hole() -> None:
    """Diagonal corner pair must not barrier-fill the interior of a wall bbox (hole island)."""

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, tile_type="UnknownTile_A"),
        _cell(3, 1, tile_type="UnknownTile_B"),
        _cell(1, 2, tile_type="UnknownTile_C"),
        _cell(3, 2, tile_type="UnknownTile_D"),
        _cell(1, 3, tile_type="UnknownTile_E"),
        _cell(3, 3, tile_type="UnknownTile_F"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    assert int(res.summary_json.get("diagonal_closed_cell_count", 0)) == 0
    assert not any(c.x == 2 and c.y == 2 for c in res.cells)


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


def test_reconstruction_does_not_fill_external_one_cell_line() -> None:
    """1-cell void between walls stays external when bbox flood reaches it."""

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, tile_type="UnknownTile_A"),
        _cell(3, 1, tile_type="UnknownTile_B"),
        _cell(1, 2, tile_type="UnknownTile_C"),
        _cell(3, 2, tile_type="UnknownTile_D"),
        _cell(1, 3, tile_type="UnknownTile_E"),
        _cell(2, 3, tile_type="UnknownTile_mid"),
        _cell(3, 3, tile_type="UnknownTile_F"),
    )
    res = reconstruct_snapshot(_snapshot(cells))
    assert not any(c.x == 2 and c.y == 2 for c in res.cells)
    assert int(res.summary_json.get("sealed_slit_cell_count", 0)) == 0
