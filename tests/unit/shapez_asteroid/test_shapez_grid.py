"""No-x0 column: adjacency and cardinal steps."""

from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.extraction.shapez_grid import (
    cardinal_unit_toward,
    cores_shapez_adjacent,
    neighbors4,
    require_cardinal_unit_toward,
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


def test_require_cardinal_unit_toward_across_x0_gap() -> None:
    assert require_cardinal_unit_toward((-1, 3), (1, 3)) == (1, 0)
    assert require_cardinal_unit_toward((1, 3), (-1, 3)) == (-1, 0)


def test_require_cardinal_unit_toward_raises_when_not_adjacent() -> None:
    with pytest.raises(ValueError, match="no legal cardinal step"):
        require_cardinal_unit_toward((1, 0), (5, 0))


def test_cardinal_unit_toward_fallback_when_not_adjacent() -> None:
    assert cardinal_unit_toward((1, 0), (5, 0)) == (1, 0)


def test_cardinal_unit_toward_across_x0_gap_matches_require() -> None:
    a, b = (-1, 2), (1, 2)
    assert cardinal_unit_toward(a, b) == require_cardinal_unit_toward(a, b) == (1, 0)


def test_neighbors4_no_zero_x() -> None:
    assert (0, 0) not in neighbors4(-1, 0)
    assert (1, 0) in neighbors4(-1, 0)
