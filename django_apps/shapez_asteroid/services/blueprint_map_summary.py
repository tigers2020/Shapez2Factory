"""Summarize 2D extraction map from decoded Shapez 2 copy payloads (island BP.Entries).

Only **extraction-relevant** entries appear in bounds and plot (miners, extensions, pumps,
extractors, boosters). Transport (belt, pipe) and foundations are classified but filtered out.

Layout math assumes **no placement at X == 0**: entries with ``X == 0`` are ignored.
See .cursor/rules/architecture.mdc (Asteroid grid).
"""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_patch_interior import (
    compute_patch_interior_cells,
)
from django_apps.shapez_asteroid.services.style_classifier import (
    PlotStyle,
    classify_layout_type,
    is_extraction_style,
)


def summarize_island_entries_map(decoded: dict[str, Any]) -> dict[str, Any]:
    """Return extraction-only entry count and X/Y bounds for ``BP["Entries"]``."""

    cells = _collect_extraction_cells(decoded)
    if not cells:
        return _empty_summary(0)

    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return {
        "entry_count": len(cells),
        "x_min": min(xs),
        "x_max": max(xs),
        "y_min": min(ys),
        "y_max": max(ys),
    }


def list_island_entry_plot_points(decoded: dict[str, Any]) -> list[dict[str, Any]]:
    """Return extraction-only plot points (non-zero ``X``).

    Each item includes ``x``, ``y``, ``t``, ``style``, and optional ``r``.
    """

    out: list[dict[str, Any]] = []
    for x_val, y_val, t_str, style, r_val in _collect_extraction_cells(decoded):
        row: dict[str, Any] = {
            "x": x_val,
            "y": y_val,
            "t": t_str,
            "style": style.value,
        }
        if r_val is not None:
            row["r"] = r_val
        out.append(row)
    return out


def list_island_patch_fill_points(decoded: dict[str, Any]) -> list[dict[str, Any]]:
    """Inferred patch interior cells (no BP entry); style ``patch_interior``."""

    cells = _collect_extraction_cells(decoded)
    if not cells:
        return []
    occupied = {(c[0], c[1]) for c in cells}
    style_val = PlotStyle.patch_interior.value
    return [
        {"x": x, "y": y, "t": None, "style": style_val}
        for x, y in compute_patch_interior_cells(occupied)
    ]


def _collect_extraction_cells(
    decoded: dict[str, Any],
) -> list[tuple[int, int, str | None, PlotStyle, int | None]]:
    bp = decoded.get("BP")
    if not isinstance(bp, dict):
        return []

    raw_entries = bp.get("Entries")
    entries: list[Any] = raw_entries if isinstance(raw_entries, list) else []

    result: list[tuple[int, int, str | None, PlotStyle, int | None]] = []
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
        assert style is not None
        r_val = _int_or_none(item.get("R"))
        result.append((x_val, y_val, t_str, style, r_val))
    return result


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
