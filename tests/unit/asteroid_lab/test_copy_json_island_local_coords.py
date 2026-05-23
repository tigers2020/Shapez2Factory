"""Copy JSON island-local coordinate rules."""

from __future__ import annotations

from django_apps.asteroid_lab.snapshots.coord_frames import IslandRawCoord
from django_apps.asteroid_lab.snapshots.copy_json_coords import (
    as_entry_int,
    entries_have_explicit_raw_x_zero,
    entry_island_local_xy,
    entry_island_raw_coord,
    entry_raw_r,
    entry_raw_x,
    entry_raw_y,
    iter_entry_dicts,
)
from django_apps.shapez_core.services.shapez_copy_decode import decode_shapez2_copy

# 3× ShapeMinerExtension + miner + belt above miner (in-game paste, 2026-05-23).
_THREE_EXT_MINER_BELT_COPY = (
    "SHAPEZ2-4-H4sIAJmKEWoA/5SQwQrCMBBE/2XwGA+1ByFHsUJBQaqIIiJLGzEQ05KkaCn5d9PmInqShYVl38zA9DiAJ0k6Z1hswXtMXNcIcORWka7AkJe1Hh5LcgR+hgw33ypyt9o8LJhulYoL9k6N4EUbBxfPkGlnpLBB2OMIPp0xnEIgwz5krKmrW3fdDbKN1MJkLye0lSHQs8gnf/D/GAewAE8jvmuoFAuh3HVVmyeZ6oM6fbE/1vCX0J3UZLqDMGPGWKj3bwEGAPvbCnpcAQAA"
)


def test_as_entry_int_defaults_missing_to_zero() -> None:
    assert as_entry_int(None) == 0
    assert as_entry_int(3) == 3


def test_entry_raw_axes_default_omitted_keys() -> None:
    row = {"Y": 1, "T": "Layout_ShapeMinerExtension"}
    assert entry_raw_x(row) == 0
    assert entry_raw_y(row) == 1
    assert entry_raw_r(row) == 0


def test_entry_island_raw_coord_wraps_entry_raw_xy() -> None:
    row = {"Y": 1, "T": "Layout_ShapeMinerExtension"}
    assert entry_island_raw_coord(row) == IslandRawCoord(0, 1)
    assert entry_island_raw_coord(row) == IslandRawCoord(*entry_island_local_xy(row))


def test_three_ext_miner_belt_copy_decodes_to_expected_island_local_xy() -> None:
    root = decode_shapez2_copy(_THREE_EXT_MINER_BELT_COPY)
    by_t = {(entry_raw_x(e), entry_raw_y(e)): e["T"] for e in iter_entry_dicts(root)}
    assert by_t[(-2, 1)] == "Layout_ShapeMinerExtension"
    assert by_t[(-1, 1)] == "Layout_ShapeMinerExtension"
    assert by_t[(0, 1)] == "Layout_ShapeMinerExtension"
    assert by_t[(1, 0)] == "SpaceBelt_Forward"
    assert by_t[(1, 1)] == "Layout_ShapeMiner"


def test_three_ext_layout_uses_raw_x_zero_column() -> None:
    root = decode_shapez2_copy(_THREE_EXT_MINER_BELT_COPY)
    rows = iter_entry_dicts(root)
    assert entries_have_explicit_raw_x_zero(rows)


