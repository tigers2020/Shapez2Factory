"""Reconstruction adapter server coord tagging (PR-C)."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.acceptance_topology import server_coord_for_cell
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import ServerCoord, server_coord_to_tuple


def test_server_coord_for_cell_returns_server_coord_dataclass() -> None:
    cell = DecodedCellDTO(
        x=1,
        y=2,
        layer=None,
        rotation=0,
        tile_type="Layout_ShapeMiner",
        cell_kind="miner",
        transport_kind="",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
        server_x=3,
        server_y=4,
    )
    got = server_coord_for_cell(cell, None)
    assert got == ServerCoord(3, 4)
    assert server_coord_to_tuple(got) == (3, 4)
