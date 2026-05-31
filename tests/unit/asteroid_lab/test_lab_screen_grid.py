"""Unit tests for ``django_apps.asteroid_lab.lab_screen_grid`` (mini-map grid + rotation deg)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.lab_screen_grid import (
    mini_map_grid_coord,
    mini_map_linear_index,
    sprite_rotation_deg_from_quarter,
)


def test_mini_map_grid_coord_row_col_linear() -> None:
    g = mini_map_grid_coord(2, 3, min_x=1, min_y=1, width=4)
    assert g.row == 2
    assert g.col == 1
    assert g.linear_index == 2 * 4 + 1


def test_mini_map_linear_index_matches_grid_coord() -> None:
    sx, sy, smx, smy, sw = 0, 1, 0, 0, 3
    assert mini_map_linear_index(sx, sy, min_x=smx, min_y=smy, width=sw) == 3


@pytest.mark.parametrize(
    ("rotation", "expected_deg"),
    [
        (0, 0),
        (1, 90),
        (2, 180),
        (3, 270),
        (-1, 270),
        (7, 270),
        (None, 0),
    ],
)
def test_sprite_rotation_deg_from_quarter(rotation: object, expected_deg: int) -> None:
    assert sprite_rotation_deg_from_quarter(rotation) == expected_deg
