"""Server dense grid → Lab raw (x, y) projection for replay timeline adapters (Phase 9C)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.replay.timeline_dtos import ReplayCell
from django_apps.asteroid_lab.snapshots.server_coords import server_xy_for_raw_xy


def dense_index_to_raw_x(dense_x: int) -> int:
    """Inverse of ``raw_x_to_dense_index`` (column 0 omitted in blueprint maps to dense 0).

    ``dense_x == 0`` → ``raw_x == 0`` is projection/display contract only; it must not be read as
    original blueprint ``raw X == 0``. Projection ``raw_x`` != original blueprint raw X.
    """

    if dense_x < 0:
        return dense_x
    if dense_x > 0:
        return dense_x + 1
    return 0


def lab_xy_from_server_xy(
    server_x: int,
    server_y: int,
    *,
    server_xy_params: tuple[int, int],
) -> tuple[int, int]:
    """Project dense server coords to Lab/raw blueprint ``(x, y)``."""

    min_dense_x, min_raw_y = int(server_xy_params[0]), int(server_xy_params[1])
    dense_x = int(server_x) + min_dense_x
    raw_x = dense_index_to_raw_x(dense_x)
    raw_y = int(server_y) + min_raw_y
    return raw_x, raw_y


def lab_xy_round_trip(
    raw_x: int,
    raw_y: int,
    *,
    server_xy_params: tuple[int, int],
) -> tuple[int, int]:
    """Return Lab ``(x, y)`` after server_xy_for_raw_xy → lab_xy_from_server_xy."""

    sx, sy = server_xy_for_raw_xy(
        int(raw_x),
        int(raw_y),
        min_dense_x=int(server_xy_params[0]),
        min_raw_y=int(server_xy_params[1]),
    )
    return lab_xy_from_server_xy(sx, sy, server_xy_params=server_xy_params)


@dataclass(frozen=True, slots=True)
class ReplayProjectionContext:
    """Adapter-only projection inputs (never algorithm input)."""

    server_xy_params: tuple[int, int]
    base_ref: str | None = None
    fallback_full_cells: tuple[ReplayCell, ...] = ()
