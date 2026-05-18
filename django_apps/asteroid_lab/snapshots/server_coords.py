"""Shapez2 asteroid map: dense x (raw +1 skips column 0) + bbox server (left-bottom origin).

Pure helpers — no Django imports. See
``documents/refactory/asteroid_server_coords_layout_fingerprint_2026-05-16.md``.
"""

from __future__ import annotations

from typing import Any

COORD_SYSTEM_BBOX_LEFT_BOTTOM = "server_bbox_left_bottom_dense_x_v1"


def raw_x_to_dense_index(raw_x: int) -> int:
    """Map raw blueprint ``X`` to a contiguous dense column index.

    Raw ``..., -2, -1, 1, 2, ...`` (no 0 column). Omitted / explicit ``X == 0`` → dense ``0``.
    """

    if raw_x < 0:
        return raw_x
    if raw_x > 0:
        return raw_x - 1
    return 0


# Backward-compatible name used across snapshots / inspection.
raw_x_to_dense_x = raw_x_to_dense_index


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
    """Mutate ``BP.Entries`` dict rows in-place: set ``server_x`` / ``server_y`` from parent bbox.

    Uses ``entry.get('X'/'Y', 0)`` semantics via ``_as_int``. Nested ``B`` / building entries are
    not scanned. Overwrites any prior ``server_x`` / ``server_y`` on each top-level dict row.
    """

    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        return decoded_json
    entries_raw = bp.get("Entries")
    entries: list[Any] = entries_raw if isinstance(entries_raw, list) else []

    dict_rows: list[dict[str, Any]] = [e for e in entries if isinstance(e, dict)]
    if not dict_rows:
        return decoded_json

    dense_vals = [raw_x_to_dense_index(_as_int(e.get("X"))) for e in dict_rows]
    raw_y_vals = [_as_int(e.get("Y")) for e in dict_rows]
    min_dense_x = min(dense_vals)
    min_raw_y = min(raw_y_vals)

    for item in dict_rows:
        raw_x = _as_int(item.get("X"))
        raw_y = _as_int(item.get("Y"))
        dense_x = raw_x_to_dense_index(raw_x)
        item["server_x"] = dense_x - min_dense_x
        item["server_y"] = raw_y - min_raw_y

    meta = decoded_json.setdefault("_asteroid_lab_coord_system", {})
    if isinstance(meta, dict):
        meta["coord_system"] = COORD_SYSTEM_BBOX_LEFT_BOTTOM
        meta["server_x_rule"] = "dense_x_minus_min_dense_x"
        meta["server_y_rule"] = "raw_y_minus_min_y"

    return decoded_json


def server_xy_for_raw_xy(
    raw_x: int,
    raw_y: int,
    *,
    min_dense_x: int,
    min_raw_y: int,
) -> tuple[int, int]:
    """Server grid coords given map bbox (left-bottom origin)."""

    dense_x = raw_x_to_dense_index(raw_x)
    return (dense_x - min_dense_x, raw_y - min_raw_y)


def map_bbox_dense_and_y(entries: list[dict[str, Any]]) -> tuple[int, int] | None:
    """Return ``(min_dense_x, min_raw_y)`` from top-level blueprint dict rows, or ``None``."""

    dense_vals: list[int] = []
    raw_y_vals: list[int] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        dense_vals.append(raw_x_to_dense_index(_as_int(item.get("X"))))
        raw_y_vals.append(_as_int(item.get("Y")))
    if not dense_vals:
        return None
    return (min(dense_vals), min(raw_y_vals))


# Backward-compatible name; same coord-system id as ``COORD_SYSTEM_BBOX_LEFT_BOTTOM``.
COORD_SYSTEM_BBOX_RIGHT_BOTTOM = COORD_SYSTEM_BBOX_LEFT_BOTTOM

__all__ = [
    "COORD_SYSTEM_BBOX_LEFT_BOTTOM",
    "COORD_SYSTEM_BBOX_RIGHT_BOTTOM",
    "attach_server_coords_to_decoded_json",
    "map_bbox_dense_and_y",
    "raw_x_to_dense_index",
    "raw_x_to_dense_x",
    "server_xy_for_raw_xy",
]
