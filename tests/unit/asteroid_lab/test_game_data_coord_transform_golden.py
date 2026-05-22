"""Golden vectors for canonical-E coord rotation (``asteroid_coord_transform_spec.md``)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.coord_transform import (
    rotate_direction,
    rotate_offset,
)
from django_apps.asteroid_lab.optimization.enums import Direction

_REFERENCE_OFFSET = (1, 0)
_REFERENCE_DIRECTION = Direction.E

# Normative table: docs/domain/asteroid_coord_transform_spec.md § Golden vectors
_OFFSET_GOLDEN: tuple[tuple[int, tuple[int, int]], ...] = (
    (0, (1, 0)),
    (1, (0, -1)),
    (2, (-1, 0)),
    (3, (0, 1)),
)

_DIRECTION_GOLDEN: tuple[tuple[int, Direction], ...] = (
    (0, Direction.E),
    (1, Direction.S),
    (2, Direction.W),
    (3, Direction.N),
)


@pytest.mark.parametrize(("steps", "expected_offset"), _OFFSET_GOLDEN)
def test_rotate_offset_golden_vectors(steps: int, expected_offset: tuple[int, int]) -> None:
    assert rotate_offset(_REFERENCE_OFFSET, steps) == expected_offset


@pytest.mark.parametrize(("steps", "expected_direction"), _DIRECTION_GOLDEN)
def test_rotate_direction_golden_vectors(steps: int, expected_direction: Direction) -> None:
    assert rotate_direction(_REFERENCE_DIRECTION, steps) is expected_direction
