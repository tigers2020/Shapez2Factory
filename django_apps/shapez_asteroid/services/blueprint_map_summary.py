"""Summarize 2D asteroid mining coordinates from decoded Shapez 2 copy payloads (island BP.Entries).

Mining-relevant entries (miners, extensions, pumps, extractors, boosters) form **one map**
with ``role: "occupied"``. Enclosed voids inferred from that perimeter use ``role: "inferred"``.

Transport (belt, pipe) are omitted from the production mining map but included in
``build_map_timeline`` step ``with_transport`` for UI playback.

Layout math assumes **no placement at X == 0**: entries with ``X == 0`` are skipped.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_patch_interior import (
    compute_patch_interior_cells,
)
from django_apps.shapez_asteroid.services.style_classifier import (
    PlotStyle,
    classify_layout_type,
    is_extraction_style,
)

EXTRACTOR_DEMOLITION_STYLES: frozenset[PlotStyle] = frozenset(
    {
        PlotStyle.extractor,
        PlotStyle.miner,
        PlotStyle.fluid_miner,
    }
)

SUPPORT_DEMOLITION_STYLES: frozenset[PlotStyle] = frozenset(
    {
        PlotStyle.extension,
        PlotStyle.fluid_extension,
        PlotStyle.booster,
    }
)


@dataclass(frozen=True)
class TimelineRow:
    """One BP coordinate row for timeline transforms.

    When ``t`` is cleared by demolition, ``source_surface`` preserves fluid vs shape for the
    resulting ``layout_kind: asteroid_field`` cell.
    """

    x: int
    y: int
    t: str | None
    r: int | None
    source_surface: str | None = None
    source_layout_kind: str | None = None


def summarize_island_entries_map(decoded: dict[str, Any]) -> dict[str, Any]:
    """Return mining-only entry count and X/Y bounds for ``BP["Entries"]``."""

    return _summary_from_timeline_rows(_mining_occupied_rows(decoded))


def list_island_mining_map(decoded: dict[str, Any]) -> list[dict[str, Any]]:
    """Single asteroid mining coordinate map: occupied blueprint cells + inferred interior.

    Shell geometry and inferred interior follow the full extraction perimeter (miners,
    extractors, extensions as placed). Occupied cells reflect **post-demolition** layouts:
    extractor and extension coordinates become ``layout_kind: asteroid_field`` (no ``t``),
    matching the last timeline step.

    Each item has ``x``, ``y``, ``role`` (``"occupied"`` | ``"inferred"``), ``surface``
    (``"shape"`` | ``"fluid"``) from layout ``T`` substrings. Occupied rows may include ``t``
    and ``r`` when present in the blueprint, and ``layout_kind`` (``PlotStyle`` value) for UI.
    """

    rows_ext = _mining_occupied_rows(decoded)
    rows_strip_all = _strip_layout_rows(rows_ext, strip_extractors=True, strip_extensions=True)
    return _mining_map_reconstructed(rows_ext, rows_strip_all)


def build_copy_preview_mining(
    decoded: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """One BP scan: summary + unified mining map (for copy-preview API)."""

    rows = _mining_occupied_rows(decoded)
    rows_strip_all = _strip_layout_rows(rows, strip_extractors=True, strip_extensions=True)
    return _summary_from_timeline_rows(rows), _mining_map_reconstructed(rows, rows_strip_all)


MAP_TIMELINE_STEP_IDS: tuple[str, ...] = (
    "with_transport",
    "extraction_shell",
    "strip_extractors",
    "strip_extensions",
    "fill_interior",
    "final",
)


def build_map_timeline(decoded: dict[str, Any]) -> list[dict[str, Any]]:
    """Six UI steps from BP entries; last step matches ``list_island_mining_map`` output."""

    rows_transport = _mining_with_transport_rows(decoded)
    rows_ext = _mining_occupied_rows(decoded)
    rows_strip_ex = _strip_layout_rows(rows_ext, strip_extractors=True, strip_extensions=False)
    rows_strip_all = _strip_layout_rows(rows_ext, strip_extractors=True, strip_extensions=True)

    final_map = _mining_map_reconstructed(rows_ext, rows_strip_all)

    return [
        {
            "id": MAP_TIMELINE_STEP_IDS[0],
            "summary": _summary_from_rows(rows_transport),
            "mining_map": _mining_map_with_transport(rows_transport),
        },
        {
            "id": MAP_TIMELINE_STEP_IDS[1],
            "summary": _summary_from_timeline_rows(rows_ext),
            "mining_map": _mining_map_occupied_only(rows_ext),
        },
        {
            "id": MAP_TIMELINE_STEP_IDS[2],
            "summary": _summary_from_timeline_rows(rows_strip_ex),
            "mining_map": _mining_map_occupied_only(rows_strip_ex),
        },
        {
            "id": MAP_TIMELINE_STEP_IDS[3],
            "summary": _summary_from_timeline_rows(rows_strip_all),
            "mining_map": _mining_map_occupied_only(rows_strip_all),
        },
        {
            "id": MAP_TIMELINE_STEP_IDS[4],
            "summary": _summary_from_timeline_rows(rows_ext),
            "mining_map": final_map,
        },
        {
            "id": MAP_TIMELINE_STEP_IDS[5],
            "summary": _summary_from_timeline_rows(rows_ext),
            "mining_map": final_map,
        },
    ]


def _summary_from_timeline_rows(rows: list[TimelineRow]) -> dict[str, Any]:
    if not rows:
        return _empty_summary(0)

    xs = [c.x for c in rows]
    ys = [c.y for c in rows]
    return {
        "entry_count": len(rows),
        "x_min": min(xs),
        "x_max": max(xs),
        "y_min": min(ys),
        "y_max": max(ys),
    }


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


def _mining_map_reconstructed(
    rows_shell: list[TimelineRow],
    rows_emit: list[TimelineRow],
) -> list[dict[str, Any]]:
    """Interior + dominant surface from full extraction shell; occupied cells from ``rows_emit``."""

    if not rows_shell:
        return []

    dominant = _dominant_mining_surface_rows(rows_shell)
    occupied_set = {(row.x, row.y) for row in rows_shell}
    out: list[dict[str, Any]] = []

    for x, y in compute_patch_interior_cells(occupied_set):
        out.append({"x": x, "y": y, "role": "inferred", "surface": dominant})

    for row in sorted(rows_emit, key=lambda r: (r.y, r.x)):
        surf = _surface_for_demolished_or_active(row, dominant)
        cell: dict[str, Any] = {
            "x": row.x,
            "y": row.y,
            "role": "occupied",
            "surface": surf,
        }
        if row.t is not None:
            cell["t"] = row.t
        if row.r is not None:
            cell["r"] = row.r
        if row.t is not None:
            _attach_layout_kind(cell, row.t)
        else:
            cell["layout_kind"] = "asteroid_field"
        out.append(cell)

    return out


def _mining_with_transport_rows(
    decoded: dict[str, Any],
) -> list[tuple[int, int, str | None, int | None]]:
    """Extraction layouts plus belt/pipe cells (same coord last-write wins)."""

    bp = decoded.get("BP")
    if not isinstance(bp, dict):
        return []

    raw_entries = bp.get("Entries")
    entries: list[Any] = raw_entries if isinstance(raw_entries, list) else []

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
        if style == PlotStyle.platform or style is None:
            continue
        if not (is_extraction_style(style) or style in (PlotStyle.belt, PlotStyle.pipe)):
            continue
        r_val = _int_or_none(item.get("R"))
        by_coord[(x_val, y_val)] = (t_str, r_val)

    return sorted(
        ((x, y, t, r) for (x, y), (t, r) in by_coord.items()),
        key=lambda row: (row[1], row[0]),
    )


def _strip_layout_rows(
    rows: list[TimelineRow],
    *,
    strip_extractors: bool,
    strip_extensions: bool,
) -> list[TimelineRow]:
    dominant = _dominant_mining_surface_rows(rows)
    out: list[TimelineRow] = []
    for row in rows:
        st = classify_layout_type(row.t)
        if strip_extractors and st in EXTRACTOR_DEMOLITION_STYLES:
            ss = _occupied_surface(row.t, dominant) if row.t else "shape"
            slk = st.value if st is not None else None
            out.append(
                TimelineRow(row.x, row.y, None, row.r, ss, slk),
            )
            continue
        if strip_extensions and st in SUPPORT_DEMOLITION_STYLES:
            ss = _occupied_surface(row.t, dominant) if row.t else "shape"
            slk = st.value if st is not None else None
            out.append(
                TimelineRow(row.x, row.y, None, row.r, ss, slk),
            )
            continue
        out.append(row)
    return sorted(out, key=lambda r: (r.y, r.x))


def _mining_map_with_transport(
    rows: list[tuple[int, int, str | None, int | None]],
) -> list[dict[str, Any]]:
    if not rows:
        return []

    ext_only = [(x, y, t, r) for x, y, t, r in rows if is_extraction_style(classify_layout_type(t))]
    dominant = _dominant_mining_surface_simple(ext_only) if ext_only else "shape"

    out: list[dict[str, Any]] = []
    for x, y, t_str, r_val in sorted(rows, key=lambda row: (row[1], row[0])):
        st = classify_layout_type(t_str)
        if st == PlotStyle.belt:
            out.append({"x": x, "y": y, "role": "belt", "surface": dominant})
        elif st == PlotStyle.pipe:
            out.append({"x": x, "y": y, "role": "pipe", "surface": dominant})
        else:
            surf = _occupied_surface(t_str, dominant)
            row: dict[str, Any] = {"x": x, "y": y, "role": "occupied", "surface": surf}
            if t_str is not None:
                row["t"] = t_str
            if r_val is not None:
                row["r"] = r_val
            _attach_layout_kind(row, t_str)
            out.append(row)
    return out


def _mining_map_occupied_only(
    rows: list[TimelineRow],
) -> list[dict[str, Any]]:
    if not rows:
        return []

    dominant = _dominant_mining_surface_rows(rows)
    out: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda r: (r.y, r.x)):
        surf = _surface_for_demolished_or_active(row, dominant)
        cell: dict[str, Any] = {
            "x": row.x,
            "y": row.y,
            "role": "occupied",
            "surface": surf,
        }
        if row.t is not None:
            cell["t"] = row.t
        if row.r is not None:
            cell["r"] = row.r
        if row.t is not None:
            _attach_layout_kind(cell, row.t)
        else:
            cell["layout_kind"] = "asteroid_field"
        out.append(cell)
    return out


def _surface_for_demolished_or_active(row: TimelineRow, dominant: str) -> str:
    if row.t is not None:
        return _occupied_surface(row.t, dominant)
    if row.source_surface is not None:
        return row.source_surface
    return "shape"


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


def _dominant_mining_surface_simple(
    rows: list[tuple[int, int, str | None, int | None]],
) -> str:
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


def _dominant_mining_surface_rows(rows: list[TimelineRow]) -> str:
    hints: list[str] = []
    for row in rows:
        if row.t is None:
            continue
        h = _surface_hint_from_layout_type(row.t)
        if h:
            hints.append(h)
    if "fluid" in hints:
        return "fluid"
    if "shape" in hints:
        return "shape"
    return "shape"


def _occupied_surface(t_str: str | None, dominant: str) -> str:
    return _surface_hint_from_layout_type(t_str) or dominant


def _attach_layout_kind(cell: dict[str, Any], t_str: str | None) -> None:
    """Expose ``PlotStyle`` for occupied blueprint cells (timeline labels / pointer)."""

    if t_str is None:
        return
    st = classify_layout_type(t_str)
    if st is not None and is_extraction_style(st):
        cell["layout_kind"] = st.value


def _mining_occupied_rows(
    decoded: dict[str, Any],
) -> list[TimelineRow]:
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
        (TimelineRow(x, y, t, r) for (x, y), (t, r) in by_coord.items()),
        key=lambda row: (row.y, row.x),
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
