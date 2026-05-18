"""Admin genetic-sample mini-map: server bbox → grid row/col (no mirror, no direction strings)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.admin_lab_sprites import normalize_lab_rotation_q


@dataclass(frozen=True)
class MiniMapGridCoord:
    """Tight server bbox: ``row``/``col`` vs ``server_min_*``; ``linear_index`` row-major."""

    row: int
    col: int
    linear_index: int


def mini_map_grid_coord(
    server_x: int,
    server_y: int,
    *,
    server_min_x: int,
    server_min_y: int,
    server_width: int,
) -> MiniMapGridCoord:
    row = int(server_y) - int(server_min_y)
    col = int(server_x) - int(server_min_x)
    return MiniMapGridCoord(
        row=row,
        col=col,
        linear_index=row * int(server_width) + col,
    )


def mini_map_linear_index(
    server_x: int,
    server_y: int,
    *,
    server_min_x: int,
    server_min_y: int,
    server_width: int,
) -> int:
    return mini_map_grid_coord(
        server_x,
        server_y,
        server_min_x=server_min_x,
        server_min_y=server_min_y,
        server_width=server_width,
    ).linear_index


def sprite_rotation_deg_from_quarter(rotation: object) -> int:
    """Domain quarter ``R`` → CSS ``rotate`` degrees (East-facing asset, CW quarter steps)."""

    return normalize_lab_rotation_q(rotation) * 90
