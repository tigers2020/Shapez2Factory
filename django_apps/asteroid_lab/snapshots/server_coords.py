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


def _parse_server_axis_str(val: str) -> int | None:
    t = val.strip()
    if not t or t.lower() == "null":
        return None
    try:
        return int(t, 10)
    except ValueError:
        return None


def coerce_server_axis_int(val: Any) -> int | None:
    """Normalize ``server_x`` / ``server_y`` from JSON or DTO (reject bool; allow int-like).

    Blueprint ``X``/``Y`` use :func:`_as_int` (bools allowed). Server axes must never treat
    ``bool`` as ``int`` (``isinstance(True, int)`` is true in Python).
    """

    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, int):
        return int(val)
    if isinstance(val, float):
        return int(val) if val.is_integer() else None
    if isinstance(val, str):
        return _parse_server_axis_str(val)
    return None


def attach_server_coords_to_decoded_json(decoded_json: dict[str, Any]) -> dict[str, Any]:
    """Mutate ``BP.Entries`` items in-place: add ``server_x`` / ``server_y``.

    Preserves ``X`` / ``Y``. Skips non-dict rows. Entries with ``X == 0`` use
    :func:`server_xy_for_layout_line_xy` (layout seam bridge; same contract as decode adapter).
    Idempotent overwrite of ``server_x`` / ``server_y`` when recomputed.
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
            lx, ly = server_xy_for_layout_line_xy(
                0, y, max_dense_x=max_dense_x, min_raw_y=min_raw_y
            )
            item["server_x"] = lx
            item["server_y"] = ly
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


def dense_x_layout_line_including_zero(x: int) -> int:
    """Dense column index for integer layout ``x`` when ``x == 0`` is allowed (world / flatten).

    Shapez2 blueprint **raw** columns omit ``x == 0``; see :func:`raw_x_to_dense_x`. Upstream may
    still attach ``X == 0`` after offsets (e.g. parent + local). Map that seam placeholder to the
    same dense index as raw ``x == -1`` so :func:`server_xy_for_layout_line_xy` stays contiguous
    with the negative branch and matches :func:`server_xy_for_raw_xy` for ``x == -1``.
    """

    if x < 0:
        return (x + 1) // 2
    if x == 0:
        return 0
    return (x - 1) // 2 + 1


def server_xy_for_layout_line_xy(
    x: int,
    raw_y: int,
    *,
    max_dense_x: int,
    min_raw_y: int,
) -> tuple[int, int]:
    """Server coords for layout ``x`` including ``x == 0`` (not only strict blueprint raw)."""

    dense_x = dense_x_layout_line_including_zero(x)
    return (max_dense_x - dense_x, raw_y - min_raw_y)


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


def _lab_row_raw_xy(item: dict[str, Any]) -> tuple[int, int] | None:
    """Lab ``full_map`` / overlay rows: lowercase ``x``/``y`` or blueprint-style ``X``/``Y``."""

    if not isinstance(item, dict):
        return None
    if "x" in item:
        return _as_int(item.get("x")), _as_int(item.get("y"))
    if "X" in item:
        return _as_int(item.get("X")), _as_int(item.get("Y"))
    return None


def map_bbox_dense_and_y_from_lab_rows(entries: list[dict[str, Any]]) -> tuple[int, int] | None:
    """Like :func:`map_bbox_dense_and_y` for Lab replay rows (``x``/``y`` keys)."""

    coords: list[tuple[int, int, int]] = []
    for item in entries:
        pair = _lab_row_raw_xy(item)
        if pair is None:
            continue
        x, y = pair
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


def raw_xy_for_server_xy(
    sx: int,
    sy: int,
    *,
    max_dense_x: int,
    min_raw_y: int,
    lab_rows: list[dict[str, Any]] | None = None,
) -> tuple[int, int]:
    """Inverse of :func:`server_xy_for_raw_xy` for Lab/UI projection.

    When ``lab_rows`` is provided, the first row whose ``(server_x, server_y)`` matches
    ``(sx, sy)`` (computed from that row's raw ``x``/``y``) wins — this disambiguates the
    two-raw-columns-per-dense strip. Otherwise use the canonical odd-raw mapping
    ``raw_x = 2 * (max_dense_x - sx) - 1`` (matches the dense column seam used with server).
    """

    t_sx, t_sy = int(sx), int(sy)
    raw_y = t_sy + int(min_raw_y)
    if lab_rows:
        for item in lab_rows:
            if not isinstance(item, dict):
                continue
            pair = _lab_row_raw_xy(item)
            if pair is None:
                continue
            rx, ry = pair
            if rx == 0:
                continue
            sp = server_xy_for_raw_xy(
                rx,
                ry,
                max_dense_x=int(max_dense_x),
                min_raw_y=int(min_raw_y),
            )
            if sp is None:
                continue
            if sp == (t_sx, t_sy):
                return (rx, ry)
    dense_x = int(max_dense_x) - t_sx
    raw_x = 2 * dense_x - 1
    return (raw_x, raw_y)


__all__ = [
    "COORD_SYSTEM_BBOX_RIGHT_BOTTOM",
    "attach_server_coords_to_decoded_json",
    "coerce_server_axis_int",
    "dense_x_layout_line_including_zero",
    "map_bbox_dense_and_y",
    "map_bbox_dense_and_y_from_lab_rows",
    "raw_xy_for_server_xy",
    "raw_x_to_dense_x",
    "server_xy_for_layout_line_xy",
    "server_xy_for_raw_xy",
]
