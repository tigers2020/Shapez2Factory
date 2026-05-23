"""Replay coordinate projection (Phase 9C; PR-F island-native frames).

Replay ``full_map`` rows use island-local ``(x, y)`` (copy JSON). ``lab_xy_from_server_xy``
remains for legacy frames that store dense ``server_x``/``server_y`` only.
"""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.replay.timeline_dtos import ReplayCell
from django_apps.asteroid_lab.snapshots.server_coords import (
    server_xy_for_raw_xy,
    unpack_server_xy_params,
)


def dense_index_to_raw_x(dense_x: int, *, has_explicit_raw_x_zero: bool = False) -> int:
    """Inverse of ``raw_x_to_dense_index`` (column 0 omitted in blueprint maps to dense 0).

    ``dense_x == 0`` → ``raw_x == 0`` is projection/display contract only; it must not be read as
    original blueprint ``raw X == 0``. Projection ``raw_x`` != original blueprint raw X.
    """

    if dense_x < 0:
        return dense_x
    if dense_x == 0:
        return 0
    if has_explicit_raw_x_zero:
        return dense_x
    return dense_x + 1


def lab_xy_from_server_xy(
    server_x: int,
    server_y: int,
    *,
    server_xy_params: tuple[int, int],
) -> tuple[int, int]:
    """Project dense server coords to Lab/raw blueprint ``(x, y)``."""

    min_dense_x, min_raw_y, has_zero = unpack_server_xy_params(server_xy_params)
    dense_x = int(server_x) + min_dense_x
    raw_x = dense_index_to_raw_x(dense_x, has_explicit_raw_x_zero=has_zero)
    raw_y = int(server_y) + min_raw_y
    return raw_x, raw_y


def lab_xy_round_trip(
    raw_x: int,
    raw_y: int,
    *,
    server_xy_params: tuple[int, int],
) -> tuple[int, int]:
    """Return Lab ``(x, y)`` after server_xy_for_raw_xy → lab_xy_from_server_xy."""

    md, my, hz = unpack_server_xy_params(server_xy_params)
    sx, sy = server_xy_for_raw_xy(
        int(raw_x),
        int(raw_y),
        min_dense_x=md,
        min_raw_y=my,
        has_explicit_raw_x_zero=hz,
    )
    return lab_xy_from_server_xy(sx, sy, server_xy_params=server_xy_params)


def lab_xy_from_replay_cell(x: int, y: int) -> tuple[int, int]:
    """Island-local replay cell coordinates (identity; PR-F canonical path)."""

    return int(x), int(y)


@dataclass(frozen=True, slots=True)
class ReplayProjectionContext:
    """Adapter-only projection inputs (never algorithm input)."""

    server_xy_params: tuple[int, int]
    base_ref: str | None = None
    fallback_full_cells: tuple[ReplayCell, ...] = ()
