"""Shapez2 asteroid map: dense x (no x==0) + bbox server (right-bottom origin).

Pure helpers — no Django imports. See
``documents/refactory/asteroid_server_coords_layout_fingerprint_2026-05-16.md``.
"""

from __future__ import annotations

from typing import Any

COORD_SYSTEM_BBOX_RIGHT_BOTTOM = "server_bbox_right_bottom_dense_x_v1"
_MSG_NO_X0 = "Shapez2 asteroid grid has no x == 0 column"


def raw_x_to_dense_x(raw_x: int) -> int:
    if raw_x == 0:
        raise ValueError(_MSG_NO_X0)
    if raw_x < 0:
        return (raw_x + 1) // 2
    return (raw_x - 1) // 2 + 1


def _as_int(val: Any) -> int:
    if val is None:
        return 0
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int):
        return val
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def attach_server_coords_to_decoded_json(decoded_json: dict[str, Any]) -> dict[str, Any]:
    """Mutate ``BP.Entries`` items in-place: add ``server_x`` / ``server_y`` where raw X is valid.

    Preserves ``X`` / ``Y``. Skips entries with ``X == 0`` or non-dict rows. Idempotent overwrite
    of ``server_x`` / ``server_y`` when recomputed.
    """

    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        return decoded_json
    entries_raw = bp.get("Entries")
    entries: list[Any] = entries_raw if isinstance(entries_raw, list) else []

    coords: list[tuple[int, int, int]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        x = _as_int(item.get("X"))
        y = _as_int(item.get("Y"))
        if x == 0:
            continue
        try:
            dx = raw_x_to_dense_x(x)
        except ValueError:
            continue
        coords.append((x, y, dx))

    if not coords:
        return decoded_json

    max_dense_x = max(t[2] for t in coords)
    min_raw_y = min(t[1] for t in coords)

    for item in entries:
        if not isinstance(item, dict):
            continue
        x = _as_int(item.get("X"))
        y = _as_int(item.get("Y"))
        if x == 0:
            item.pop("server_x", None)
            item.pop("server_y", None)
            continue
        try:
            dense_x = raw_x_to_dense_x(x)
        except ValueError:
            item.pop("server_x", None)
            item.pop("server_y", None)
            continue
        item["server_x"] = max_dense_x - dense_x
        item["server_y"] = y - min_raw_y

    meta = decoded_json.setdefault("_asteroid_lab_coord_system", {})
    if isinstance(meta, dict):
        meta["coord_system"] = COORD_SYSTEM_BBOX_RIGHT_BOTTOM
        meta["server_y_rule"] = "raw_y_minus_min_y"

    return decoded_json


def server_xy_for_raw_xy(
    raw_x: int,
    raw_y: int,
    *,
    max_dense_x: int,
    min_raw_y: int,
) -> tuple[int, int] | None:
    """Single-cell server coords given map bbox parameters; ``None`` if ``raw_x == 0``."""

    if raw_x == 0:
        return None
    dense_x = raw_x_to_dense_x(raw_x)
    return (max_dense_x - dense_x, raw_y - min_raw_y)


def map_bbox_dense_and_y(entries: list[dict[str, Any]]) -> tuple[int, int] | None:
    """Return ``(max_dense_x, min_raw_y)`` from valid top-level blueprint entries, or ``None``."""

    coords: list[tuple[int, int, int]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        x = _as_int(item.get("X"))
        y = _as_int(item.get("Y"))
        if x == 0:
            continue
        try:
            dx = raw_x_to_dense_x(x)
        except ValueError:
            continue
        coords.append((x, y, dx))
    if not coords:
        return None
    return (max(t[2] for t in coords), min(t[1] for t in coords))


__all__ = [
    "COORD_SYSTEM_BBOX_RIGHT_BOTTOM",
    "attach_server_coords_to_decoded_json",
    "map_bbox_dense_and_y",
    "raw_x_to_dense_x",
    "server_xy_for_raw_xy",
]
