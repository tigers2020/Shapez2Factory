"""No-x0 column: adjacency and cardinal steps."""

from __future__ import annotations

from django_apps.shapez_asteroid.extraction.shapez_grid import (
    cores_shapez_adjacent,
    neighbors4,
    shapez_manhattan,
    step_cardinal,
)


def test_step_east_skips_x0_from_minus1() -> None:
    assert step_cardinal(-1, -6, 1, 0) == (1, -6)


def test_step_west_skips_x0_from_plus1() -> None:
    assert step_cardinal(1, 3, -1, 0) == (-1, 3)


def test_minus1_and_plus1_are_layout_adjacent() -> None:
    assert cores_shapez_adjacent((-1, -6), (1, -6))
    assert shapez_manhattan((-1, -6), (1, -6)) == 1


def test_neighbors4_no_zero_x() -> None:
    assert (0, 0) not in neighbors4(-1, 0)
    assert (1, 0) in neighbors4(-1, 0)
