"""Shapez2 copy JSON island-local coordinates (``BP.Entries``).

Decoded paste / export JSON uses a **blueprint island local** grid — not asteroid
world tiles, not lab ``server_x``/``server_y``, not reconstruction world map coords.

Normative rules (verified against in-game paste, 2026-05-23):

- Omitted ``X`` / ``Y`` / ``R`` → ``0``.
- ``X + 1`` → one cell to the **right** on screen.
- ``Y + 1`` → one cell **down** on screen.
- ``X == 0`` is a valid column in copy JSON (unlike lab world map ``x == 0``).

See ``documents/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md``
and ``docs/superpowers/specs/2026-05-23-coordinate-tagged-frames-design.md``.

Tagged boundary: :func:`entry_island_raw_coord` → :class:`~coord_frames.IslandRawCoord`.
Lab ``server_x`` / ``server_y`` from :mod:`server_coords` remain **deprecated** dense
projection until PR-F.
"""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.snapshots.coord_frames import IslandRawCoord

COPY_JSON_AXIS_X_RIGHT = "copy_json_x_increases_screen_right"
COPY_JSON_AXIS_Y_DOWN = "copy_json_y_increases_screen_down"


def as_entry_int(val: Any) -> int:
    """Coerce a blueprint entry numeric field; missing / null → ``0``."""

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


def entry_raw_x(entry: dict[str, Any]) -> int:
    """Island-local ``X`` (omitted key → ``0``)."""

    return as_entry_int(entry.get("X"))


def entry_raw_y(entry: dict[str, Any]) -> int:
    """Island-local ``Y`` (omitted key → ``0``)."""

    return as_entry_int(entry.get("Y"))


def entry_raw_r(entry: dict[str, Any]) -> int:
    """Island-local rotation ``R`` (omitted key → ``0``)."""

    return as_entry_int(entry.get("R"))


def entry_island_local_xy(entry: dict[str, Any]) -> tuple[int, int]:
    """``(x, y)`` after defaulting omitted keys."""

    return (entry_raw_x(entry), entry_raw_y(entry))


def entry_island_raw_coord(entry: dict[str, Any]) -> IslandRawCoord:
    """Island-local paste coord as :class:`~coord_frames.IslandRawCoord`."""

    x, y = entry_island_local_xy(entry)
    return IslandRawCoord(x, y)


def entries_have_explicit_raw_x_zero(entries: list[dict[str, Any]]) -> bool:
    """Whether any entry uses raw column ``X == 0``.

    Includes entries with **omitted** ``X`` (decoded as ``0``). When true,
    :func:`django_apps.asteroid_lab.snapshots.server_coords.raw_x_to_dense_index`
    keeps positive ``X`` values distinct from column ``0`` (no ``1`` → dense ``0`` collapse).
    """

    return any(entry_raw_x(row) == 0 for row in entries)


def iter_entry_dicts(decoded_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Top-level ``BP.Entries`` dict rows only (no nested ``B`` scan)."""

    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        return []
    entries_raw = bp.get("Entries")
    if not isinstance(entries_raw, list):
        return []
    return [row for row in entries_raw if isinstance(row, dict)]


__all__ = [
    "COPY_JSON_AXIS_X_RIGHT",
    "COPY_JSON_AXIS_Y_DOWN",
    "as_entry_int",
    "entries_have_explicit_raw_x_zero",
    "entry_island_local_xy",
    "entry_island_raw_coord",
    "entry_raw_r",
    "entry_raw_x",
    "entry_raw_y",
    "iter_entry_dicts",
]
