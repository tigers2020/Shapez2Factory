"""HTML mini-map for :class:`~django_apps.asteroid_lab.models.GeneSeed` admin (readonly)."""

from __future__ import annotations

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
from django_apps.asteroid_lab.snapshots.island_bbox import island_bbox_from_cells

# Change-form preview: larger cells. Changelist uses same cell size inside a scroll box.
_DEFAULT_CELL_PX = 52
_GAP_PX = 2
# Admin grid: never smaller than this (empty cells if blueprint bbox is tighter).
_MIN_ADMIN_GRID_COLS = 4
_MIN_ADMIN_GRID_ROWS = 4
# Changelist column: scroll viewport matches min grid so ~4횞4 cells fit before scroll.
_LIST_VIEWPORT_COLS = _MIN_ADMIN_GRID_COLS
_LIST_VIEWPORT_ROWS = _MIN_ADMIN_GRID_ROWS
# Matches inner ``.genetic-sample-mini-map`` padding (6px 횞 2).
_INNER_PAD_PX = 12


def _list_viewport_max_px(*, cell_px: int) -> tuple[int, int]:
    """``for_list`` outer box: max-width / max-height so ~cols횞rows cells fit before scroll."""

    g = _GAP_PX
    p = _INNER_PAD_PX
    w = _LIST_VIEWPORT_COLS * cell_px + (_LIST_VIEWPORT_COLS - 1) * g + p
    h = _LIST_VIEWPORT_ROWS * cell_px + (_LIST_VIEWPORT_ROWS - 1) * g + p
    return w, h


def _mini_map_cell_block(
    at_cell: DecodedCellDTO, *, cell_px: int, img_px: int
) -> tuple[SafeString | str, str, int]:
    """One ``lab_sprite_resolve`` call ??inner HTML, ``data-sprite`` relpath, rotation degrees."""

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


def _mini_map_cell_radius_px(cell_px: int) -> int:
    """Match Lab ``--lab-cell-radius``: round(cellPx * 0.14), clamp [2, 7]."""

    return max(2, min(7, round(cell_px * 0.14)))


def _genetic_sample_mini_map_cell_div(
    *,
    x: int,
    y: int,
    coord: MiniMapGridCoord,
    inner: SafeString | str,
    sprite_relpath: str,
    rot_deg: int,
    cell_px: int,
) -> SafeString:
    radius_px = _mini_map_cell_radius_px(cell_px)
    return format_html(
        '<div class="genetic-sample-mini-map-cell" '
        'data-raw-x="{}" data-raw-y="{}" '
        'data-grid-row="{}" data-grid-col="{}" data-linear-index="{}" data-sprite="{}" '
        'data-rotation-deg="{}" style="background:#020617;border:1px solid #1e293b;'
        'border-radius:{}px;display:flex;align-items:center;justify-content:center;overflow:hidden;">'
        "{}</div>",
        x,
        y,
        coord.row,
        coord.col,
        coord.linear_index,
        sprite_relpath,
        rot_deg,
        radius_px,
        inner,
    )


def _genetic_sample_mini_map_cells_html(
    *,
    width: int,
    height: int,
    min_x: int,
    min_y: int,
    by_pos: dict[tuple[int, int], DecodedCellDTO],
    cell_px: int,
    img_px: int,
) -> list[SafeString]:
    cells_html: list[SafeString] = []
    # Row 0 at top = smallest raw Y. Grid order is defined by
    # ``mini_map_grid_coord``; tests assert it matches this loop (no rotation mixed into row/col).
    for grid_r in range(height):
        for grid_c in range(width):
            x = min_x + grid_c
            y = min_y + grid_r
            coord = mini_map_grid_coord(
                x,
                y,
                min_x=min_x,
                min_y=min_y,
                width=width,
            )
            at_cell = by_pos.get((grid_c, grid_r))
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
                    x=x,
                    y=y,
                    coord=coord,
                    inner=inner,
                    sprite_relpath=sprite_relpath,
                    rot_deg=rot_deg,
                    cell_px=cell_px,
                )
            )
    return cells_html


def genetic_sample_mini_map_html(
    decoded_json: dict[str] | None,
    *,
    cell_px: int = _DEFAULT_CELL_PX,
    for_list: bool = False,
) -> SafeString | str:
    """CSS grid of blueprint cells; optional ``img`` from ``web/assets/sprites/``.

    ``for_list``: wrap in a bounded viewport (at least ~4횞4 cells at default ``cell_px``)
    with scroll.
    The drawn grid is at least 4횞4 even when the blueprint bbox is smaller (empty cells).
    """

    if not decoded_json or not isinstance(decoded_json.get("BP"), dict):
        return "-"

    snap = build_decoded_blueprint_snapshot(decoded_json)
    if not snap.cells:
        return "-"

    # Admin preview: bbox from decoded cells only (island-local X/Y, X==0 allowed).
    # Do not trust persisted reconstruction meta — legacy rows used export/server extents.
    bbox = island_bbox_from_cells(snap.cells) or snap.bbox_json
    _bbox_keys = ("min_x", "min_y", "width", "height")
    if not all(k in bbox for k in _bbox_keys):
        bbox = snap.bbox_json
    if not all(k in bbox for k in _bbox_keys):
        return mark_safe(
            '<p class="genetic-sample-map-note">No island bbox; cannot draw mini-map.</p>'
        )

    try:
        min_x = int(bbox["min_x"])
        min_y = int(bbox["min_y"])
        sw = max(int(bbox["width"]), _MIN_ADMIN_GRID_COLS)
        sh = max(int(bbox["height"]), _MIN_ADMIN_GRID_ROWS)
    except (KeyError, TypeError, ValueError):
        return mark_safe(
            '<p class="genetic-sample-map-note">Invalid island bbox; cannot draw mini-map.</p>'
        )

    by_pos: dict[tuple[int, int], DecodedCellDTO] = {}
    for cell in snap.cells:
        by_pos[(int(cell.x) - min_x, int(cell.y) - min_y)] = cell

    img_px = max(18, cell_px - 6)
    style = (
        "display:grid;"
        f"grid-template-columns:repeat({sw},{cell_px}px);"
        f"grid-template-rows:repeat({sh},{cell_px}px);"
        f"gap:{_GAP_PX}px;width:max-content;background:#0f172a;padding:6px;border-radius:8px;"
    )

    cells_html = _genetic_sample_mini_map_cells_html(
        width=sw,
        height=sh,
        min_x=min_x,
        min_y=min_y,
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
