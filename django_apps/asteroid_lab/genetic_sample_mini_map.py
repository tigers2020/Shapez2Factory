"""HTML mini-map for :class:`~django_apps.asteroid_lab.models.GeneticSample` admin (readonly)."""

from __future__ import annotations

from typing import Any

from django.templatetags.static import static
from django.utils.html import format_html, format_html_join
from django.utils.safestring import SafeString, mark_safe

from django_apps.asteroid_lab.admin_lab_sprites import lab_sprite_resolve
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)

# Change-form preview: larger cells. Changelist uses same cell size inside a scroll box.
_DEFAULT_CELL_PX = 44
_GAP_PX = 2


def _mini_map_cell_inner(at_cell: DecodedCellDTO, *, cell_px: int, img_px: int) -> SafeString | str:
    relpath, rot_q = lab_sprite_resolve(
        tile_type=at_cell.tile_type,
        cell_kind=at_cell.cell_kind,
        rotation=at_cell.rotation,
    )
    deg = rot_q * 90
    if relpath:
        url = static(f"web/assets/sprites/{relpath}")
        return format_html(
            '<img src="{}" alt="" width="{}" height="{}" draggable="false" '
            'style="display:block;margin:auto;transform-origin:center center;'
            'transform:rotate({}deg);" />',
            url,
            img_px,
            img_px,
            deg,
        )
    t_val = (at_cell.tile_type or "").strip() or "?"
    fs = max(7, min(11, cell_px // 4))
    span_style = (
        f"font-size:{fs}px;line-height:1.05;color:#94a3b8;display:block;"
        f"max-width:{cell_px - 2}px;max-height:{cell_px - 2}px;overflow:hidden;"
        "text-overflow:ellipsis;word-break:break-all;text-align:center;"
    )
    return format_html('<span title="{}" style="{}">{}</span>', t_val, span_style, t_val)


def genetic_sample_mini_map_html(
    decoded_json: dict[str, Any] | None,
    *,
    cell_px: int = _DEFAULT_CELL_PX,
    for_list: bool = False,
) -> SafeString | str:
    """CSS grid of blueprint cells; optional ``img`` from ``web/assets/sprites/``.

    ``for_list``: wrap in a fixed viewport with scroll so changelist rows stay bounded.
    """

    if not decoded_json or not isinstance(decoded_json.get("BP"), dict):
        return "-"

    snap = build_decoded_blueprint_snapshot(decoded_json)
    bbox = snap.bbox_json
    if "server_width" not in bbox or "server_height" not in bbox:
        return mark_safe(
            '<p class="genetic-sample-map-note">server 좌표가 없어 미니맵을 그릴 수 없습니다.</p>'
        )

    sw = int(bbox["server_width"])
    sh = int(bbox["server_height"])
    sminx = int(bbox["server_min_x"])
    smaxy = int(bbox["server_max_y"])

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

    cells_html: list[SafeString] = []
    for grid_r in range(sh):
        sy = smaxy - grid_r
        for grid_c in range(sw):
            sx = sminx + grid_c
            at_cell = by_pos.get((sx, sy))
            if at_cell is None:
                inner: SafeString | str = ""
            else:
                inner = _mini_map_cell_inner(at_cell, cell_px=cell_px, img_px=img_px)
            cells_html.append(
                format_html(
                    '<div style="background:#020617;border:1px solid #1e293b;'
                    'display:flex;align-items:center;justify-content:center;overflow:hidden;">'
                    "{}</div>",
                    inner,
                )
            )

    inner_map = format_html(
        '<div class="genetic-sample-mini-map" style="{}">{}</div>',
        mark_safe(style),
        format_html_join("", "{}", ((c,) for c in cells_html)),
    )
    if not for_list:
        return inner_map

    wrap_style = (
        "max-width:min(100%,360px);max-height:140px;overflow:auto;"
        "border:1px solid #334155;border-radius:6px;background:#020617;"
        "vertical-align:middle;line-height:0;"
    )
    return format_html('<div style="{}">{}</div>', mark_safe(wrap_style), inner_map)
