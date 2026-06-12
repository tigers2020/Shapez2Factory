"""Asteroid map coordinate invariants (no x == 0 column)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.snapshots.asteroid_map_coords import (
    iter_four_neighbors_map,
    left_of,
    neighbors4_world,
    right_of,
    visual_col,
    world_raw_coord,
)
from django_apps.asteroid_lab.snapshots.coord_frames import WorldRawCoord
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)
from django_apps.asteroid_lab.snapshots.existing_layout_inspection import inspect_existing_layout


def test_visual_col_mapping() -> None:
    assert visual_col(-3) == -3
    assert visual_col(-1) == -1
    assert visual_col(1) == 0
    assert visual_col(2) == 1
    assert visual_col(3) == 2


def test_visual_col_zero_rejected() -> None:
    with pytest.raises(ValueError, match="no x == 0"):
        visual_col(0)


def test_left_right_of_seam() -> None:
    assert left_of(1) == -1
    assert right_of(-1) == 1
    assert left_of(2) == 1
    assert right_of(1) == 2


def test_world_raw_coord_rejects_x_zero() -> None:
    with pytest.raises(ValueError, match="x == 0"):
        world_raw_coord(0, 1)


def test_neighbors4_world_matches_map_cardinals() -> None:
    c = WorldRawCoord(-1, 2)
    nbrs = neighbors4_world(c)
    assert WorldRawCoord(1, 2) in nbrs
    assert WorldRawCoord(-2, 2) in nbrs
    assert WorldRawCoord(-1, 3) in nbrs
    assert WorldRawCoord(-1, 1) in nbrs


def test_iter_four_neighbors_skips_x_zero() -> None:
    n = list(iter_four_neighbors_map(-1, 0, None))
    assert (1, 0, None) in n
    assert (0, 0, None) not in n


def test_iter_four_neighbors_at_world_x_zero_is_empty() -> None:
    assert list(iter_four_neighbors_map(0, 0, None)) == []


def test_transport_bfs_connects_across_seam() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": -1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Right"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    fluid = [c for c in ins.transport_components if c.transport_kind == "space_pipe"]
    assert len(fluid) == 1
    assert fluid[0].cell_count == 2
