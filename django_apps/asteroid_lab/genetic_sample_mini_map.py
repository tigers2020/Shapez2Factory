"""HTML mini-map for :class:`~django_apps.asteroid_lab.models.GeneticSample` admin (readonly)."""

from __future__ import annotations

from typing import Any

from django.templatetags.static import static
from django.utils.html import format_html, format_html_join
from django.utils.safestring import SafeString, mark_safe

from django_apps.asteroid_lab.admin_lab_sprites import lab_sprite_resolve
from django_apps.asteroid_lab.lab_screen_grid import (
    MiniMapGridCoord,
    mini_map_grid_coord,
    sprite_rotation_deg_from_quarter,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)

# Change-form preview: larger cells. Changelist uses same cell size inside a scroll box.
_DEFAULT_CELL_PX = 44
_GAP_PX = 2
# Admin grid: never smaller than this (empty cells if blueprint bbox is tighter).
_MIN_ADMIN_GRID_COLS = 4
_MIN_ADMIN_GRID_ROWS = 4
# Changelist column: scroll viewport matches min grid so ~4×4 cells fit before scroll.
_LIST_VIEWPORT_COLS = _MIN_ADMIN_GRID_COLS
_LIST_VIEWPORT_ROWS = _MIN_ADMIN_GRID_ROWS
# Matches inner ``.genetic-sample-mini-map`` padding (6px × 2).
_INNER_PAD_PX = 12


def _list_viewport_max_px(*, cell_px: int) -> tuple[int, int]:
    """``for_list`` outer box: max-width / max-height so ~cols×rows cells fit before scroll."""

    g = _GAP_PX
    p = _INNER_PAD_PX
    w = _LIST_VIEWPORT_COLS * cell_px + (_LIST_VIEWPORT_COLS - 1) * g + p
    h = _LIST_VIEWPORT_ROWS * cell_px + (_LIST_VIEWPORT_ROWS - 1) * g + p
    return w, h


def _mini_map_cell_block(
    at_cell: DecodedCellDTO, *, cell_px: int, img_px: int
) -> tuple[SafeString | str, str, int]:
    """One ``lab_sprite_resolve`` call → inner HTML, ``data-sprite`` relpath, rotation degrees."""

    relpath, _ = lab_sprite_resolve(
        tile_type=at_cell.tile_type,
        cell_kind=at_cell.cell_kind,
        rotation=at_cell.rotation,
    )
    deg = sprite_rotation_deg_from_quarter(at_cell.rotation)
    sprite_relpath = relpath or ""
    if relpath:
        url = static(f"web/assets/sprites/{relpath}")
        inner: SafeString | str = format_html(
            '<img src="{}" alt="" width="{}" height="{}" draggable="false" '
            'style="display:block;margin:auto;transform-origin:center center;'
            'transform:rotate({}deg);" />',
            url,
            img_px,
            img_px,
            deg,
        )
        return inner, sprite_relpath, deg
    t_val = (at_cell.tile_type or "").strip() or "?"
    fs = max(7, min(11, cell_px // 4))
    span_style = (
        f"font-size:{fs}px;line-height:1.05;color:#94a3b8;display:block;"
        f"max-width:{cell_px - 2}px;max-height:{cell_px - 2}px;overflow:hidden;"
        "text-overflow:ellipsis;word-break:break-all;text-align:center;"
    )
    inner = format_html('<span title="{}" style="{}">{}</span>', t_val, span_style, t_val)
    return inner, sprite_relpath, deg


def _genetic_sample_mini_map_cell_div(
    *,
    sx: int,
    sy: int,
    coord: MiniMapGridCoord,
    inner: SafeString | str,
    sprite_relpath: str,
    rot_deg: int,
) -> SafeString:
    return format_html(
        '<div class="genetic-sample-mini-map-cell" '
        'data-server-x="{}" data-server-y="{}" '
        'data-grid-row="{}" data-grid-col="{}" data-linear-index="{}" data-sprite="{}" '
        'data-rotation-deg="{}" style="background:#020617;border:1px solid #1e293b;'
        'display:flex;align-items:center;justify-content:center;overflow:hidden;">'
        "{}</div>",
        sx,
        sy,
        coord.row,
        coord.col,
        coord.linear_index,
        sprite_relpath,
        rot_deg,
        inner,
    )


def _genetic_sample_mini_map_cells_html(
    *,
    sw: int,
    sh: int,
    sminx: int,
    sminy: int,
    by_pos: dict[tuple[int, int], DecodedCellDTO],
    cell_px: int,
    img_px: int,
) -> list[SafeString]:
    cells_html: list[SafeString] = []
    # Row 0 at top = smallest server_y (= smallest raw Y). Grid order is defined by
    # ``mini_map_grid_coord``; tests assert it matches this loop (no rotation mixed into row/col).
    for grid_r in range(sh):
        sy = sminy + grid_r
        for grid_c in range(sw):
            sx = sminx + grid_c
            coord = mini_map_grid_coord(
                sx,
                sy,
                server_min_x=sminx,
                server_min_y=sminy,
                server_width=sw,
            )
            at_cell = by_pos.get((sx, sy))
            if at_cell is None:
                inner = ""
                sprite_relpath = ""
                rot_deg = 0
            else:
                inner, sprite_relpath, rot_deg = _mini_map_cell_block(
                    at_cell, cell_px=cell_px, img_px=img_px
                )
            cells_html.append(
                _genetic_sample_mini_map_cell_div(
                    sx=sx,
                    sy=sy,
                    coord=coord,
                    inner=inner,
                    sprite_relpath=sprite_relpath,
                    rot_deg=rot_deg,
                )
            )
    return cells_html


def genetic_sample_mini_map_html(
    decoded_json: dict[str, Any] | None,
    *,
    cell_px: int = _DEFAULT_CELL_PX,
    for_list: bool = False,
) -> SafeString | str:
    """CSS grid of blueprint cells; optional ``img`` from ``web/assets/sprites/``.

    ``for_list``: wrap in a bounded viewport (at least ~4×4 cells at default ``cell_px``)
    with scroll.
    The drawn grid is at least 4×4 even when the blueprint bbox is smaller (empty cells).
    """

    if not decoded_json or not isinstance(decoded_json.get("BP"), dict):
        return "-"

    snap = build_decoded_blueprint_snapshot(decoded_json)
    bbox = snap.bbox_json
    if "server_width" not in bbox or "server_height" not in bbox:
        return mark_safe(
            '<p class="genetic-sample-map-note">server 좌표가 없어 미니맵을 그릴 수 없습니다.</p>'
        )

    sw = max(int(bbox["server_width"]), _MIN_ADMIN_GRID_COLS)
    sh = max(int(bbox["server_height"]), _MIN_ADMIN_GRID_ROWS)
    sminx = int(bbox["server_min_x"])
    sminy = int(bbox["server_min_y"])

    by_pos: dict[tuple[int, int], DecodedCellDTO] = {}
    for cell in snap.cells:
        if cell.server_x is None or cell.server_y is None:
            continue
        by_pos[(int(cell.server_x), int(cell.server_y))] = cell

    img_px = max(18, cell_px - 6)
    style = (
        "display:grid;"
        f"grid-template-columns:repeat({sw},{cell_px}px);"
        f"grid-template-rows:repeat({sh},{cell_px}px);"
        f"gap:{_GAP_PX}px;width:max-content;background:#0f172a;padding:6px;border-radius:8px;"
    )

    cells_html = _genetic_sample_mini_map_cells_html(
        sw=sw,
        sh=sh,
        sminx=sminx,
        sminy=sminy,
        by_pos=by_pos,
        cell_px=cell_px,
        img_px=img_px,
    )

    inner_map = format_html(
        '<div class="genetic-sample-mini-map" style="{}">{}</div>',
        mark_safe(style),
        format_html_join("", "{}", ((c,) for c in cells_html)),
    )
    if not for_list:
        return inner_map

    vw, vh = _list_viewport_max_px(cell_px=cell_px)
    wrap_style = (
        f"min-width:{vw}px;max-width:min(100%,360px);max-height:{vh}px;overflow:auto;"
        "border:1px solid #334155;border-radius:6px;background:#020617;"
        "vertical-align:middle;line-height:0;"
    )
    return format_html('<div style="{}">{}</div>', mark_safe(wrap_style), inner_map)
