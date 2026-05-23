"""Project copy JSON island-local raw ``X``/``Y`` into lab server bbox coordinates.

**Deprecated (PR-F):** ``server_x`` / ``server_y`` dense bbox — use
``copy_json_coords.entry_island_raw_coord`` at paste boundaries until
``CoordFrame`` promotion (design spec: ``docs/superpowers/specs/``).

Input ``BP.Entries`` ``X``/``Y`` are **island blueprint local** (see
``copy_json_coords``). This module maps them to contiguous ``server_x`` /
``server_y`` for fingerprints and optimization — not asteroid world tiles.

Pure helpers — no Django imports. See
``documents/research/research_asteroid_server_coords_layout_fingerprint_2026-05-16.md``.
"""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.snapshots.copy_json_coords import (
    as_entry_int,
    entries_have_explicit_raw_x_zero,
    entry_raw_x,
    entry_raw_y,
)

COORD_SYSTEM_BBOX_LEFT_BOTTOM = "server_bbox_left_bottom_dense_x_v1"


def unpack_server_xy_params(params: tuple[int, ...] | None) -> tuple[int, int, bool]:
    """``(min_dense_x, min_raw_y[, has_explicit_raw_x_zero])`` from persisted params."""

    if params is None:
        return 0, 0, False
    md = int(params[0])
    my = int(params[1]) if len(params) > 1 else 0
    hz = bool(params[2]) if len(params) > 2 else False
    return md, my, hz


def raw_x_to_dense_index(raw_x: int, *, has_explicit_raw_x_zero: bool = False) -> int:
    """Map raw blueprint ``X`` to a contiguous dense column index.

    Raw ``..., -2, -1, 1, 2, ...`` normally omit column 0; positive ``X`` compress with
    ``X - 1``. When the map also contains explicit ``X == 0`` (game seam column), positive
    ``X`` keeps its value so ``0`` and ``1`` do not share a dense column.
    """

    if raw_x < 0:
        return raw_x
    if raw_x == 0:
        return 0
    if has_explicit_raw_x_zero:
        return raw_x
    return raw_x - 1


# Backward-compatible name used across snapshots / inspection.
raw_x_to_dense_x = raw_x_to_dense_index


def attach_server_coords_to_decoded_json(decoded_json: dict[str, Any]) -> dict[str, Any]:
    """Mutate ``BP.Entries`` dict rows in-place: set ``server_x`` / ``server_y`` from parent bbox.

    Reads island-local raw ``X``/``Y`` via ``entry_raw_x`` / ``entry_raw_y`` (omitted → 0).
    Nested ``B`` / building entries are not scanned. Overwrites any prior ``server_x`` /
    ``server_y`` on each top-level dict row.
    """

    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        return decoded_json
    entries_raw = bp.get("Entries")
    entries: list[Any] = entries_raw if isinstance(entries_raw, list) else []

    dict_rows: list[dict[str, Any]] = [e for e in entries if isinstance(e, dict)]
    if not dict_rows:
        return decoded_json

    has_zero = entries_have_explicit_raw_x_zero(dict_rows)
    dense_vals = [
        raw_x_to_dense_index(entry_raw_x(e), has_explicit_raw_x_zero=has_zero) for e in dict_rows
    ]
    raw_y_vals = [entry_raw_y(e) for e in dict_rows]
    min_dense_x = min(dense_vals)
    min_raw_y = min(raw_y_vals)

    for item in dict_rows:
        raw_x = entry_raw_x(item)
        raw_y = entry_raw_y(item)
        dense_x = raw_x_to_dense_index(raw_x, has_explicit_raw_x_zero=has_zero)
        item["server_x"] = dense_x - min_dense_x
        item["server_y"] = raw_y - min_raw_y

    meta = decoded_json.setdefault("_asteroid_lab_coord_system", {})
    if isinstance(meta, dict):
        meta["coord_system"] = COORD_SYSTEM_BBOX_LEFT_BOTTOM
        meta["server_x_rule"] = "dense_x_minus_min_dense_x"
        meta["server_y_rule"] = "raw_y_minus_min_y"
        meta["has_explicit_raw_x_zero"] = has_zero

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
    min_dense_x: int,
    min_raw_y: int,
    has_explicit_raw_x_zero: bool = False,
) -> tuple[int, int]:
    """Server grid coords given map bbox (left-bottom origin)."""

    dense_x = raw_x_to_dense_index(raw_x, has_explicit_raw_x_zero=has_explicit_raw_x_zero)
    return (dense_x - min_dense_x, raw_y - min_raw_y)


def jsonl_coord_fields(
    raw_x: int,
    raw_y: int,
    *,
    server_xy_params: tuple[int, int] | None,
) -> dict[str, Any]:
    """Explicit ``raw_*`` / ``server_*`` keys for boundary JSONL (avoids ``x`` ambiguity).

    When ``server_xy_params`` is ``None``, ``server_x`` / ``server_y`` are JSON ``null``.
    """

    out: dict[str, Any] = {"raw_x": int(raw_x), "raw_y": int(raw_y)}
    if server_xy_params is not None:
        md, my, hz = unpack_server_xy_params(server_xy_params)
        sx, sy = server_xy_for_raw_xy(
            int(raw_x), int(raw_y), min_dense_x=md, min_raw_y=my, has_explicit_raw_x_zero=hz
        )
        out["server_x"] = int(sx)
        out["server_y"] = int(sy)
    else:
        out["server_x"] = None
        out["server_y"] = None
    return out


def full_map_row_for_boundary_jsonl(
    row: dict[str, Any],
    *,
    server_xy_params: tuple[int, int] | None,
) -> dict[str, Any]:
    """Copy a replay ``full_map`` row and attach ``jsonl_coord_fields`` from its ``x``/``y``."""

    merged = dict(row)
    merged.update(
        jsonl_coord_fields(int(row["x"]), int(row["y"]), server_xy_params=server_xy_params)
    )
    return merged


def map_bbox_dense_and_y(entries: list[dict[str, Any]]) -> tuple[int, int, bool] | None:
    """Return ``(min_dense_x, min_raw_y, has_explicit_raw_x_zero)`` or ``None``."""

    dict_rows = [item for item in entries if isinstance(item, dict)]
    if not dict_rows:
        return None
    has_zero = entries_have_explicit_raw_x_zero(dict_rows)
    dense_vals: list[int] = []
    raw_y_vals: list[int] = []
    for item in dict_rows:
        dense_vals.append(
            raw_x_to_dense_index(entry_raw_x(item), has_explicit_raw_x_zero=has_zero)
        )
        raw_y_vals.append(entry_raw_y(item))
    return (min(dense_vals), min(raw_y_vals), has_zero)


# Backward-compatible name; same coord-system id as ``COORD_SYSTEM_BBOX_LEFT_BOTTOM``.
COORD_SYSTEM_BBOX_RIGHT_BOTTOM = COORD_SYSTEM_BBOX_LEFT_BOTTOM

__all__ = [
    "COORD_SYSTEM_BBOX_LEFT_BOTTOM",
    "COORD_SYSTEM_BBOX_RIGHT_BOTTOM",
    "as_entry_int",
    "attach_server_coords_to_decoded_json",
    "entries_have_explicit_raw_x_zero",
    "entry_raw_x",
    "entry_raw_y",
    "full_map_row_for_boundary_jsonl",
    "jsonl_coord_fields",
    "map_bbox_dense_and_y",
    "raw_x_to_dense_index",
    "raw_x_to_dense_x",
    "server_xy_for_layout_line_xy",
    "server_xy_for_raw_xy",
    "unpack_server_xy_params",
]
