"""Phase 9C ??server dense grid ??Lab raw projection tests."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.replay.projection_context import (
    ReplayProjectionContext,
    dense_index_to_raw_x,
    lab_xy_from_server_xy,
    lab_xy_round_trip,
)
from django_apps.asteroid_lab.snapshots.server_coords import server_xy_for_raw_xy


def test_dense_index_to_raw_x_inverse() -> None:
    assert dense_index_to_raw_x(-2) == -2
    assert dense_index_to_raw_x(0) == 0
    assert dense_index_to_raw_x(1) == 2
    assert dense_index_to_raw_x(5) == 6


def test_server_to_lab_and_round_trip_nonzero_raw_x() -> None:
    params = (1, 0)
    raw_x, raw_y = 2, 3
    sx, sy = server_xy_for_raw_xy(raw_x, raw_y, min_dense_x=params[0], min_raw_y=params[1])
    lx, ly = lab_xy_from_server_xy(sx, sy, server_xy_params=params)
    assert (lx, ly) == (raw_x, raw_y)
    assert lab_xy_round_trip(raw_x, raw_y, server_xy_params=params) == (raw_x, raw_y)


def test_server_to_lab_dense_zero_column() -> None:
    params = (0, 0)
    sx, sy = server_xy_for_raw_xy(0, 1, min_dense_x=0, min_raw_y=0)
    assert lab_xy_from_server_xy(sx, sy, server_xy_params=params) == (0, 1)


def test_replay_projection_context_is_frozen() -> None:
    ctx = ReplayProjectionContext(server_xy_params=(1, 0))
    with pytest.raises(AttributeError):
        ctx.server_xy_params = (2, 0)  # type: ignore[misc]
