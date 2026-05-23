"""Island-local bbox helpers (PR-F Wave C)."""

from __future__ import annotations

from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.island_bbox import (
    island_bbox_from_cells,
    island_bbox_from_xy_dicts,
)


def test_island_bbox_from_cells_tight_extent() -> None:
    cells = (
        DecodedCellDTO(
            x=0,
            y=-1,
            layer=None,
            rotation=0,
            tile_type="Layout_FluidMiner",
            cell_kind="miner",
            transport_kind="none",
            has_nested_blueprint=False,
            nested_entry_count=0,
            nested_type_counts_json={},
            raw_entry_json={},
            server_x=None,
            server_y=None,
        ),
        DecodedCellDTO(
            x=1,
            y=-1,
            layer=None,
            rotation=0,
            tile_type="SpacePipe_Forward",
            cell_kind="transport",
            transport_kind="forward",
            has_nested_blueprint=False,
            nested_entry_count=0,
            nested_type_counts_json={},
            raw_entry_json={},
            server_x=None,
            server_y=None,
        ),
    )
    bb = island_bbox_from_cells(cells)
    assert bb == {
        "min_x": 0,
        "max_x": 1,
        "min_y": -1,
        "max_y": -1,
        "width": 2,
        "height": 1,
    }


def test_island_bbox_from_xy_dicts_empty_returns_none() -> None:
    assert island_bbox_from_xy_dicts([]) is None
