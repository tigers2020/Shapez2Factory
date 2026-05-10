"""Shape miner rotation ↔ output cell round-trip (cardinal belt convention)."""

from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import (
    output_offset_r,
    rotation_r_for_output_direction,
    shape_miner_output_cell,
)
from django_apps.shapez_asteroid.extraction.shapez_grid import step_cardinal


@pytest.mark.parametrize(
    ("dx", "dy"),
    ((1, 0), (-1, 0), (0, 1), (0, -1)),
)
def test_rotation_r_output_round_trip(dx: int, dy: int) -> None:
    """``shape_miner_output_cell(core, r)`` matches ``step_cardinal`` for each cardinal."""

    r = rotation_r_for_output_direction(dx, dy)
    assert output_offset_r(r) == (dx, dy)
    core = (-3, 2)
    out = shape_miner_output_cell(core, r)
    assert out == step_cardinal(core[0], core[1], dx, dy)


def test_rotation_r_rejects_non_cardinal() -> None:
    with pytest.raises(ValueError):
        rotation_r_for_output_direction(1, 1)
