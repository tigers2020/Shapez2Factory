"""Admin genetic-sample mini-map: island bbox -> grid row/col."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.admin_lab_sprites import normalize_lab_rotation_q


@dataclass(frozen=True)
class MiniMapGridCoord:
    """Tight island bbox: ``row``/``col`` vs ``min_*``; ``linear_index`` row-major."""

    row: int
    col: int
    linear_index: int


def mini_map_grid_coord(
    x: int,
    y: int,
    *,
    min_x: int,
    min_y: int,
    width: int,
) -> MiniMapGridCoord:
    row = int(y) - int(min_y)
    col = int(x) - int(min_x)
    return MiniMapGridCoord(
        row=row,
        col=col,
        linear_index=row * int(width) + col,
    )


def mini_map_linear_index(
    x: int,
    y: int,
    *,
    min_x: int,
    min_y: int,
    width: int,
) -> int:
    return mini_map_grid_coord(
        x,
        y,
        min_x=min_x,
        min_y=min_y,
        width=width,
    ).linear_index


def sprite_rotation_deg_from_quarter(rotation: object) -> int:
    """Domain quarter ``R`` -> CSS ``rotate`` degrees (East-facing asset, CW quarter steps)."""

    return normalize_lab_rotation_q(rotation) * 90
