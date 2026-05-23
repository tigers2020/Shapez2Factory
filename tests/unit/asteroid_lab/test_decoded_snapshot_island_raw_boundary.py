"""Decode path uses ``entry_island_raw_coord`` (P1 — same numeric x/y as before)."""

from __future__ import annotations

from django_apps.asteroid_lab.snapshots.copy_json_coords import entry_island_raw_coord
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)
from django_apps.shapez_core.services.shapez_copy_decode import decode_shapez2_copy

_COPY = (
    "SHAPEZ2-4-H4sIAJmKEWoA/5SQwQrCMBBE/2XwGA+1ByFHsUJBQaqIIiJLGzEQ05KkaCn5d9PmInqShYVl38zA9DiAJ0k6Z1hswXtMXNcIcORWka7AkJe1Hh5LcgR+hgw33ypyt9o8LJhulYoL9k6N4EUbBxfPkGlnpLBB2OMIPp0xnEIgwz5krKmrW3fdDbKN1MJkLye0lSHQs8gnf/D/GAewAE8jvmuoFAuh3HVVmyeZ6oM6fbE/1vCX0J3UZLqDMGPGWKj3bwEGAPvbCnpcAQAA"
)


def test_build_decoded_snapshot_cell_xy_matches_island_raw_coord() -> None:
    snap = build_decoded_blueprint_snapshot(decode_shapez2_copy(_COPY))
    for cell in snap.cells:
        island = entry_island_raw_coord(cell.raw_entry_json)
        assert cell.x == island.x
        assert cell.y == island.y


def test_build_decoded_snapshot_does_not_attach_server_xy_on_dto() -> None:
    snap = build_decoded_blueprint_snapshot(decode_shapez2_copy(_COPY))
    assert snap.cells
    for cell in snap.cells:
        assert cell.server_x is None
        assert cell.server_y is None
    assert "server_min_x" not in snap.bbox_json
