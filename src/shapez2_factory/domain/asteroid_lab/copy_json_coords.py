"""Shapez2 copy JSON island-local coordinates (``BP.Entries``).

Decoded paste / export JSON uses a **blueprint island local** grid, not asteroid
world tiles and not reconstruction world map coords.

Normative rules (verified against in-game paste, 2026-05-23):

- Omitted ``X`` / ``Y`` / ``R`` → ``0``.
- ``X + 1`` → one cell to the **right** on screen.
- ``Y + 1`` → one cell **down** on screen.
- ``X == 0`` is a valid column in copy JSON (unlike lab world map ``x == 0``).

See ``documents/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md``
and ``documents/superpowers/specs/2026-05-23-coordinate-tagged-frames-design.md``.

Tagged boundary: :func:`entry_island_raw_coord` → :class:`~coord_frames.IslandRawCoord`.
Export-column projection is kept here because it is a copy JSON serialization rule,
not a runtime coordinate frame.
"""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.coord_frames import IslandRawCoord
from shapez2_factory.domain.asteroid_lab.wire_coerce import wire_int

COPY_JSON_AXIS_X_RIGHT = "copy_json_x_increases_screen_right"
COPY_JSON_AXIS_Y_DOWN = "copy_json_y_increases_screen_down"


def as_entry_int(val: object) -> int:
    """Coerce a blueprint entry numeric field; missing / null → ``0``."""

    return wire_int(val)


def entry_raw_x(entry: dict[str, object]) -> int:
    """Island-local ``X`` (omitted key → ``0``)."""

    return as_entry_int(entry.get("X"))


def entry_raw_y(entry: dict[str, object]) -> int:
    """Island-local ``Y`` (omitted key → ``0``)."""

    return as_entry_int(entry.get("Y"))


def entry_raw_r(entry: dict[str, object]) -> int:
    """Island-local rotation ``R`` (omitted key → ``0``)."""

    return as_entry_int(entry.get("R"))


def entry_island_local_xy(entry: dict[str, object]) -> tuple[int, int]:
    """``(x, y)`` after defaulting omitted keys."""

    return (entry_raw_x(entry), entry_raw_y(entry))


def entry_island_raw_coord(entry: dict[str, object]) -> IslandRawCoord:
    """Island-local paste coord as :class:`~coord_frames.IslandRawCoord`."""

    x, y = entry_island_local_xy(entry)
    return IslandRawCoord(x, y)


def entries_have_explicit_raw_x_zero(entries: list[dict[str, object]]) -> bool:
    """Whether any entry uses raw column ``X == 0``.

    Includes entries with **omitted** ``X`` (decoded as ``0``). When true,
    export-column projection keeps positive ``X`` values distinct from column ``0``.
    """

    return any(entry_raw_x(row) == 0 for row in entries)


def raw_x_to_export_column(raw_x: int, *, has_explicit_raw_x_zero: bool = False) -> int:
    """Map copy JSON ``X`` to the compact official-export column.

    이 변환은 파일 내보내기용 열 번호 계산에만 쓰며, 런타임 좌표 프레임으로
    저장하거나 DTO에 싣지 않는다.
    """

    if raw_x < 0:
        return raw_x
    if raw_x == 0:
        return 0
    if has_explicit_raw_x_zero:
        return raw_x
    return raw_x - 1


def iter_entry_dicts(decoded_json: dict[str, object]) -> list[dict[str, object]]:
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
    "raw_x_to_export_column",
]
