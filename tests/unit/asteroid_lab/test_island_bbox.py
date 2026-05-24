"""Island-local bbox helpers (PR-F Wave C)."""

from __future__ import annotations

from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.island_bbox import (
    full_map_island_bbox_from_decoded_json,
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


_LEGACY_BBOX = {
    "min_x": 0,
    "max_x": 2,
    "min_y": -1,
    "max_y": 0,
    "width": 3,
    "height": 2,
}


def test_full_map_island_bbox_ignores_legacy_server_bbox_meta() -> None:
    decoded_json = {
        "_asteroid_lab_reconstruction": {"full_map_server_bbox": dict(_LEGACY_BBOX)},
        "BP": {"Entries": []},
    }
    assert full_map_island_bbox_from_decoded_json(decoded_json) is None


def test_full_map_island_bbox_prefers_island_over_legacy_server_meta() -> None:
    island_only = {
        "min_x": 1,
        "max_x": 1,
        "min_y": 1,
        "max_y": 1,
        "width": 1,
        "height": 1,
    }
    decoded_json = {
        "_asteroid_lab_reconstruction": {
            "full_map_island_bbox": dict(island_only),
            "full_map_server_bbox": dict(_LEGACY_BBOX),
        },
        "BP": {"Entries": []},
    }
    assert full_map_island_bbox_from_decoded_json(decoded_json) == island_only


def test_full_map_island_bbox_computes_from_bp_entries_without_meta() -> None:
    """Read-compat: legacy rows without ``full_map_island_bbox`` meta still get extent from X/Y."""

    decoded_json = {
        "BP": {
            "Entries": [
                {"X": 2, "Y": 3, "T": "UnknownTile_A"},
                {"X": 5, "Y": 7, "T": "UnknownTile_B"},
            ],
        },
    }
    assert full_map_island_bbox_from_decoded_json(decoded_json) == {
        "min_x": 2,
        "max_x": 5,
        "min_y": 3,
        "max_y": 7,
        "width": 4,
        "height": 5,
    }


def test_reconstructed_export_writes_full_map_island_bbox_not_server_on_entries() -> None:
    from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
        build_reconstructed_blueprint_root,
    )

    cell = DecodedCellDTO(
        x=1,
        y=0,
        layer=None,
        rotation=0,
        tile_type="SpacePipe_Forward",
        cell_kind="transport",
        transport_kind="forward",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"X": 1, "Y": 0, "T": "SpacePipe_Forward"},
    )
    root = build_reconstructed_blueprint_root(
        (cell,),
        full_map_island_bbox={
            "min_x": 1,
            "max_x": 1,
            "min_y": 0,
            "max_y": 0,
            "width": 1,
            "height": 1,
        },
    )
    meta = root["_asteroid_lab_reconstruction"]
    assert "full_map_island_bbox" in meta
