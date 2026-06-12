"""Raster admin changelist thumbnails for reconstructed maps (display-only)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from io import BytesIO

from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)

ADMIN_LIST_THUMBNAIL_RENDERER_VERSION = "1"
ADMIN_LIST_THUMBNAIL_MAX_GRID = 48
ADMIN_LIST_THUMBNAIL_MAX_EDGE_PX = 256

_CELL_KIND_FILL: dict[str, tuple[int, int, int]] = {
    "space_belt": (51, 65, 85),
    "space_pipe": (14, 165, 233),
    "shape_miner": (245, 158, 11),
    "shape_miner_extension": (217, 119, 6),
    "fluid_miner": (56, 189, 248),
    "fluid_miner_extension": (2, 132, 199),
    "unknown": (100, 116, 139),
}
_BG_RGB = (15, 23, 42)


def canonical_decoded_json_hash(decoded_json: dict[str, object]) -> str:
    payload = json.dumps(decoded_json, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ListThumbnailWindow:
    min_x: int
    min_y: int
    grid_w: int
    grid_h: int
    truncated: bool
    cell_count: int


def compute_list_thumbnail_window(decoded_json: dict[str, object]) -> ListThumbnailWindow | None:
    if not decoded_json or not isinstance(decoded_json.get("BP"), dict):
        return None
    snap = build_decoded_blueprint_snapshot(decoded_json)
    bbox = snap.bbox_json
    if not bbox or int(bbox.get("width", 0)) < 1 or int(bbox.get("height", 0)) < 1:
        return None
    bbox_min_x = int(bbox["min_x"])
    bbox_min_y = int(bbox["min_y"])
    bbox_max_x = int(bbox["max_x"])
    bbox_max_y = int(bbox["max_y"])
    min_x = bbox_min_x
    min_y = bbox_min_y
    w = int(bbox["width"])
    h = int(bbox["height"])
    truncated = w > ADMIN_LIST_THUMBNAIL_MAX_GRID or h > ADMIN_LIST_THUMBNAIL_MAX_GRID
    if truncated:
        cap = ADMIN_LIST_THUMBNAIL_MAX_GRID
        cx = sum(c.x for c in snap.cells) // max(len(snap.cells), 1)
        cy = sum(c.y for c in snap.cells) // max(len(snap.cells), 1)
        min_x = max(bbox_min_x, min(cx - cap // 2, bbox_max_x - cap + 1))
        min_y = max(bbox_min_y, min(cy - cap // 2, bbox_max_y - cap + 1))
        w = min(cap, bbox_max_x - min_x + 1)
        h = min(cap, bbox_max_y - min_y + 1)
    return ListThumbnailWindow(
        min_x=min_x,
        min_y=min_y,
        grid_w=w,
        grid_h=h,
        truncated=truncated,
        cell_count=len(snap.cells),
    )


def _fill_for_cell(cell: DecodedCellDTO) -> tuple[int, int, int]:
    if cell.cell_kind in _CELL_KIND_FILL:
        return _CELL_KIND_FILL[cell.cell_kind]
    t = (cell.tile_type or "").strip()
    if t.startswith("SpaceBelt"):
        return _CELL_KIND_FILL["space_belt"]
    if t.startswith("SpacePipe"):
        return _CELL_KIND_FILL["space_pipe"]
    return _CELL_KIND_FILL["unknown"]


def render_list_thumbnail_image_bytes(decoded_json: dict[str, object]) -> tuple[bytes, str]:
    """Return (image_bytes, extension) where extension is webp or png."""

    from PIL import Image  # noqa: PLC0415

    win = compute_list_thumbnail_window(decoded_json)
    if win is None:
        msg = "decoded_json not drawable for list thumbnail"
        raise ValueError(msg)
    snap = build_decoded_blueprint_snapshot(decoded_json)
    cell_px = max(
        4,
        min(
            32,
            ADMIN_LIST_THUMBNAIL_MAX_EDGE_PX // max(win.grid_w, win.grid_h),
        ),
    )
    gap = 1
    img_w = win.grid_w * cell_px + (win.grid_w - 1) * gap
    img_h = win.grid_h * cell_px + (win.grid_h - 1) * gap
    img = Image.new("RGB", (img_w, img_h), _BG_RGB)
    by_xy: dict[tuple[int, int], DecodedCellDTO] = {(c.x, c.y): c for c in snap.cells}
    for gy in range(win.grid_h):
        for gx in range(win.grid_w):
            x = win.min_x + gx
            y = win.min_y + gy
            cell = by_xy.get((x, y))
            if cell is None:
                continue
            left = gx * (cell_px + gap)
            top = (win.grid_h - 1 - gy) * (cell_px + gap)
            color = _fill_for_cell(cell)
            for px in range(left, left + cell_px):
                for py in range(top, top + cell_px):
                    img.putpixel((px, py), color)
    buf = BytesIO()
    try:
        img.save(buf, format="WEBP", lossless=True)
        return buf.getvalue(), "webp"
    except OSError:
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue(), "png"


__all__ = [
    "ADMIN_LIST_THUMBNAIL_MAX_EDGE_PX",
    "ADMIN_LIST_THUMBNAIL_MAX_GRID",
    "ADMIN_LIST_THUMBNAIL_RENDERER_VERSION",
    "ListThumbnailWindow",
    "canonical_decoded_json_hash",
    "compute_list_thumbnail_window",
    "render_list_thumbnail_image_bytes",
]
