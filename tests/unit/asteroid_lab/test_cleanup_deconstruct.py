"""Unit tests for ``django_apps.asteroid_lab.cleanup`` deconstruction."""

from __future__ import annotations

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.evidence import is_asteroid_evidence
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


def test_wall_coords_union_decode_evidence_and_miner_extension() -> None:
    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, tile_type="UnknownTile_A"),
        _cell(2, 1, tile_type="UnknownTile_B"),
    )
    r = deconstruct_snapshot(_snapshot(cells))
    assert (2, 0) not in r.wall_coords
    assert (1, 0) in r.wall_coords
    assert (3, 0) in r.wall_coords
    assert (1, 1) in r.wall_coords
    assert all(is_asteroid_evidence(c) for c in r.cleaned_cells if (c.x, c.y) in {(1, 1), (2, 1)})


def test_original_cells_match_snapshot_input() -> None:
    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
    )
    r = deconstruct_snapshot(_snapshot(cells))
    assert r.original_cells == cells


def test_ignored_transport_subset_of_removed() -> None:
    cells = (
        _cell(1, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(2, 0, cell_kind="fluid_miner"),
    )
    r = deconstruct_snapshot(_snapshot(cells))
    assert len(r.ignored_transport_cells) == 1
    assert len(r.removed_building_cells) == 2
    assert len(r.cleaned_cells) == 0
