"""Seed layout orientation aligned with lab raw grid (north = decreasing y)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.seed_orient import (
    SeedLayout,
    layout_seed_at_anchor,
    placement_extension_rotation,
    placement_output_rotation,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.equipment_bundles import ports_compatible


def _single_miner_map(
    *,
    anchor: tuple[int, int],
    extension: tuple[int, int],
    north_void: tuple[int, int],
) -> ReconstructionCompleteMap:
    field = frozenset({anchor, extension})
    external_void = frozenset({north_void})
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=2,
        fluid_field_cell_count=0,
        external_void_cells=external_void,
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def test_void_to_north_commits_output_n_and_rotation_three() -> None:
    anchor = (11, -9)
    complete_map = _single_miner_map(
        anchor=anchor,
        extension=(11, -8),
        north_void=(11, -10),
    )
    layout = layout_seed_at_anchor(
        seed_id="rim_greedy_m1e1",
        anchor=anchor,
        output_dir="N",
        complete_map=complete_map,
    )
    assert isinstance(layout, SeedLayout)
    assert layout.output_dir == "N"
    assert layout.rotation == 3
    assert layout.rotation == placement_output_rotation("N")
    assert layout.m_output_stub == (11, -10)
    assert layout.extension_cells == frozenset({(11, -8)})


def test_extension_rotation_allows_island_x_zero_column() -> None:
    miner = (0, 5)
    extension = (0, 6)
    miner_r = placement_output_rotation("E")
    ext_r = placement_extension_rotation(
        miner_coord=miner,
        extension_coord=extension,
        miner_rotation=miner_r,
    )
    assert ports_compatible(
        "shape_miner_extension",
        ext_r,
        "shape_miner",
        miner_r,
        "n",
    )


def test_extension_rotation_faces_parent_miner() -> None:
    miner = (11, -9)
    extension = (11, -8)
    miner_r = placement_output_rotation("N")
    ext_r = placement_extension_rotation(
        miner_coord=miner,
        extension_coord=extension,
        miner_rotation=miner_r,
    )
    assert ports_compatible(
        "shape_miner_extension",
        ext_r,
        "shape_miner",
        miner_r,
        "n",
    )
