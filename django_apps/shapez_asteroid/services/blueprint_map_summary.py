"""Summarize 2D asteroid mining coordinates from decoded Shapez 2 copy payloads (island BP.Entries).

Mining-relevant entries (miners, extensions, pumps, extractors, boosters) form **one map**
with ``role: "occupied"``. Enclosed voids inferred from that perimeter use ``role: "inferred"``.

Transport (belt, pipe) and foundations are ignored. Layout math assumes **no placement at X == 0**:
entries with ``X == 0`` are skipped.
"""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_patch_interior import (
    compute_patch_interior_cells,
)
from django_apps.shapez_asteroid.services.style_classifier import (
    classify_layout_type,
    is_extraction_style,
)


def summarize_island_entries_map(decoded: dict[str, Any]) -> dict[str, Any]:
    """Return mining-only entry count and X/Y bounds for ``BP["Entries"]``."""

    return _summary_from_rows(_mining_occupied_rows(decoded))


def list_island_mining_map(decoded: dict[str, Any]) -> list[dict[str, Any]]:
    """Single asteroid mining coordinate map: occupied blueprint cells + inferred interior.

    Each item has ``x``, ``y``, ``role`` (``"occupied"`` | ``"inferred"``), ``surface``
    (``"shape"`` | ``"fluid"``) from layout ``T`` substrings. Occupied rows may include ``t``
    and ``r`` when present in the blueprint.
    """

    return _mining_map_from_rows(_mining_occupied_rows(decoded))


def build_copy_preview_mining(
    decoded: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """One BP scan: summary + unified mining map (for copy-preview API)."""

    rows = _mining_occupied_rows(decoded)
    return _summary_from_rows(rows), _mining_map_from_rows(rows)


def _summary_from_rows(
    rows: list[tuple[int, int, str | None, int | None]],
) -> dict[str, Any]:
    if not rows:
        return _empty_summary(0)

    xs = [c[0] for c in rows]
    ys = [c[1] for c in rows]
    return {
        "entry_count": len(rows),
        "x_min": min(xs),
        "x_max": max(xs),
        "y_min": min(ys),
        "y_max": max(ys),
    }


def _mining_map_from_rows(
    rows: list[tuple[int, int, str | None, int | None]],
) -> list[dict[str, Any]]:
    if not rows:
        return []

    dominant = _dominant_mining_surface(rows)
    occupied_set = {(x, y) for x, y, _, _ in rows}
    out: list[dict[str, Any]] = []

    for x, y in compute_patch_interior_cells(occupied_set):
        out.append({"x": x, "y": y, "role": "inferred", "surface": dominant})

    for x, y, t_str, r_val in rows:
        surf = _occupied_surface(t_str, dominant)
        row: dict[str, Any] = {"x": x, "y": y, "role": "occupied", "surface": surf}
        if t_str is not None:
            row["t"] = t_str
        if r_val is not None:
            row["r"] = r_val
        out.append(row)

    return out


def _surface_hint_from_layout_type(t: str | None) -> str | None:
    """Rough shape vs fluid hint from blueprint ``T`` (substring)."""

    if not t:
        return None
    low = t.lower()
    if "fluid" in low or "pump" in low:
        return "fluid"
    if "shape" in low:
        return "shape"
    return None


def _dominant_mining_surface(
    rows: list[tuple[int, int, str | None, int | None]],
) -> str:
    """Patch-wide surface for inferred cells; prefers fluid if any fluid mining layout."""

    hints: list[str] = []
    for _x, _y, t_str, _r in rows:
        h = _surface_hint_from_layout_type(t_str)
        if h:
            hints.append(h)
    if "fluid" in hints:
        return "fluid"
    if "shape" in hints:
        return "shape"
    return "shape"


def _occupied_surface(t_str: str | None, dominant: str) -> str:
    return _surface_hint_from_layout_type(t_str) or dominant


def _mining_occupied_rows(
    decoded: dict[str, Any],
) -> list[tuple[int, int, str | None, int | None]]:
    bp = decoded.get("BP")
    if not isinstance(bp, dict):
        return []

    raw_entries = bp.get("Entries")
    entries: list[Any] = raw_entries if isinstance(raw_entries, list) else []

    # Last occurrence per (x, y) wins; deterministic order by (y, x) for output.
    by_coord: dict[tuple[int, int], tuple[str | None, int | None]] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        x_val = _int_or_none(item.get("X"))
        if x_val is None or x_val == 0:
            continue
        y_val = _int_or_none(item.get("Y"))
        if y_val is None:
            y_val = 0
        t_raw = item.get("T")
        if isinstance(t_raw, str):
            t_str: str | None = t_raw
        elif t_raw is None:
            t_str = None
        else:
            t_str = str(t_raw)
        style = classify_layout_type(t_str)
        if not is_extraction_style(style):
            continue
        r_val = _int_or_none(item.get("R"))
        by_coord[(x_val, y_val)] = (t_str, r_val)

    return sorted(
        ((x, y, t, r) for (x, y), (t, r) in by_coord.items()),
        key=lambda row: (row[1], row[0]),
    )


def _empty_summary(entry_count: int) -> dict[str, Any]:
    return {
        "entry_count": entry_count,
        "x_min": None,
        "x_max": None,
        "y_min": None,
        "y_max": None,
    }


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
