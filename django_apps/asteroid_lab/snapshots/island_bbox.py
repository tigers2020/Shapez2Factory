"""Island-local bbox helpers (PR-F Wave C). Pure — no Django imports."""

from __future__ import annotations

from collections.abc import Sequence

from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.copy_json_coords import entry_island_raw_coord

_RECON_META_KEY = "_asteroid_lab_reconstruction"


def island_bbox_from_xy_dicts(rows: Sequence[dict[str, object]]) -> dict[str, int] | None:
    xs: list[int] = []
    ys: list[int] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        x_val: int | None = None
        y_val: int | None = None
        try:
            x_val = int(row["x"])
            y_val = int(row["y"])
        except (KeyError, TypeError, ValueError):
            try:
                x_val = int(row["X"])
                y_val = int(row["Y"])
            except (KeyError, TypeError, ValueError):
                continue
        if x_val is None or y_val is None:
            continue
        xs.append(x_val)
        ys.append(y_val)
    if not xs or not ys:
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


def full_map_island_bbox_from_decoded_json(
    decoded_json: dict[str, object],
) -> dict[str, int] | None:
    """Read persisted reconstruction meta or compute from ``BP.Entries`` island X/Y."""

    meta = decoded_json.get(_RECON_META_KEY)
    if isinstance(meta, dict):
        bb = meta.get("full_map_island_bbox")
        _bbox_keys = ("min_x", "max_x", "min_y", "max_y", "width", "height")
        if isinstance(bb, dict) and all(k in bb for k in _bbox_keys):
            try:
                return {k: int(bb[k]) for k in _bbox_keys}
            except (TypeError, ValueError):
                pass
    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        return None
    entries = bp.get("Entries")
    if not isinstance(entries, list):
        return None
    # Island-local: omitted ``X``/``Y`` default to 0 (``entry_island_raw_coord``), not skipped.
    return island_bbox_from_xy_dicts(
        [
            {"x": entry_island_raw_coord(e).x, "y": entry_island_raw_coord(e).y}
            for e in entries
            if isinstance(e, dict)
        ]
    )


__all__ = [
    "full_map_island_bbox_from_decoded_json",
    "island_bbox_from_cells",
    "island_bbox_from_xy_dicts",
]
