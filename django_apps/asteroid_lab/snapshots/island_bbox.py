"""Island-local bbox helpers (PR-F Wave C). Pure — no Django imports."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from django_apps.asteroid_lab.services.dto import DecodedCellDTO

_RECON_META_KEY = "_asteroid_lab_reconstruction"


def island_bbox_from_xy_dicts(rows: Sequence[dict[str, Any]]) -> dict[str, int] | None:
    xs: list[int] = []
    ys: list[int] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            xs.append(int(row["x"]))
            ys.append(int(row["y"]))
        except (KeyError, TypeError, ValueError):
            try:
                xs.append(int(row["X"]))
                ys.append(int(row["Y"]))
            except (KeyError, TypeError, ValueError):
                continue
    if not xs:
        return None
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "width": max_x - min_x + 1,
        "height": max_y - min_y + 1,
    }


def island_bbox_from_cells(cells: Sequence[DecodedCellDTO]) -> dict[str, int] | None:
    return island_bbox_from_xy_dicts([{"x": c.x, "y": c.y} for c in cells])


def full_map_island_bbox_from_decoded_json(decoded_json: dict[str, Any]) -> dict[str, int] | None:
    """Read persisted reconstruction meta or compute from ``BP.Entries`` island X/Y."""

    meta = decoded_json.get(_RECON_META_KEY)
    if isinstance(meta, dict):
        bb = meta.get("full_map_island_bbox")
        if isinstance(bb, dict) and "min_x" in bb and "width" in bb:
            return {
                k: int(bb[k])
                for k in ("min_x", "max_x", "min_y", "max_y", "width", "height")
            }
    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        return None
    entries = bp.get("Entries")
    if not isinstance(entries, list):
        return None
    return island_bbox_from_xy_dicts(
        [{"X": e.get("X"), "Y": e.get("Y")} for e in entries if isinstance(e, dict)]
    )


__all__ = [
    "full_map_island_bbox_from_decoded_json",
    "island_bbox_from_cells",
    "island_bbox_from_xy_dicts",
]
