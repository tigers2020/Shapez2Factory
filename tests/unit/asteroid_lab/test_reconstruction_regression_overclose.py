"""Regression: narrow external channels must not be overclosed by morphology fill."""

from __future__ import annotations

from pathlib import Path

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.evidence import is_asteroid_evidence
from django_apps.asteroid_lab.reconstruction.grid import Coord
from django_apps.asteroid_lab.reconstruction.pipeline import (
    reconstruct_snapshot,
    run_topology_reconstruction,
)
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)
from django_apps.asteroid_lab.snapshots.transport_components import is_transport_tile

_FIELD_KINDS = frozenset({"asteroid_shape_field", "asteroid_fluid_field"})

# External 1-cell-wide vertical seam (x=6) on regression fixture; must stay unfilled.
EXTERNAL_CHANNEL_COORDS: frozenset[Coord] = frozenset(
    {
        (6, -10),
        (6, -9),
        (6, -8),
        (6, -6),
        (6, -5),
        (6, -4),
        (6, -3),
        (6, -2),
        (6, -1),
    }
)

# Fully enclosed hole in synthetic hole-island layout.
ENCLOSED_INTERIOR_COORDS: frozenset[Coord] = frozenset({(2, 2)})


def _fixture_copy(name: str) -> str:
    p = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / name
    return p.read_text(encoding="utf-8").splitlines()[0].strip()


def _snapshot_from_fixture(name: str) -> DecodedBlueprintSnapshotDTO:
    code = _fixture_copy(name).removesuffix("$")
    norm = normalize_decoded_blueprint(decode_copy_string(code))
    return build_decoded_blueprint_snapshot(norm.decoded_json)


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
            "max_y": mn_y,
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


def test_reconstruction_sample_does_not_overclose_one_cell_channels() -> None:
    snap = _snapshot_from_fixture("regression_narrow_external_channels.txt")
    res = reconstruct_snapshot(snap)
    filled = _filled_field_coords(res.cells)

    for coord in EXTERNAL_CHANNEL_COORDS:
        assert coord not in filled

    s = res.summary_json
    assert int(s["sealed_slit_cell_count"]) == 0
    assert int(s["inferred_shell_cell_count"]) == 0
    preserved = int(s["external_void_preserved_count"])
    assert preserved >= len(EXTERNAL_CHANNEL_COORDS)


def test_reconstruction_internal_hole_still_fills() -> None:
    res = reconstruct_snapshot(_snapshot(_hole_island_cells()))
    filled = _filled_field_coords(res.cells)

    for coord in ENCLOSED_INTERIOR_COORDS:
        assert coord in filled

    assert int(res.summary_json["interior_patch_filled_count"]) >= len(ENCLOSED_INTERIOR_COORDS)


def test_reconstruction_no_recursive_shell_closure() -> None:
    snap = _snapshot_from_fixture("regression_narrow_external_channels.txt")
    cleanup = deconstruct_snapshot(snap)
    res = run_topology_reconstruction(cleanup)
    s = res.summary_json

    assert int(s["inferred_shell_cell_count"]) == 0
    assert int(s["sealed_slit_cell_count"]) == 0
    walls = int(s["wall_cell_count"])
    diagonal = int(s["diagonal_closed_cell_count"])
    barrier = int(s["barrier_cell_count"])
    assert barrier == walls + diagonal


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


def test_reconstruction_miner_extension_are_evidence() -> None:
    cells = (
        _cell(1, 2, cell_kind="fluid_miner"),
        _cell(3, 2, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
    )
    cleanup = deconstruct_snapshot(_snapshot(cells))
    assert (1, 2) in cleanup.wall_coords
    assert (3, 2) in cleanup.wall_coords
    res = reconstruct_snapshot(_snapshot(cells))
    assert (2, 2) not in _filled_field_coords(res.cells)
    assert int(res.summary_json["sealed_slit_cell_count"]) == 0
