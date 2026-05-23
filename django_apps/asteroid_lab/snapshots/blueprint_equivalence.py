"""Decoded blueprint layout equivalence (ORM-free, translation-invariant for miners).

Horizontal comparison uses compact export columns, while vertical offset uses raw ``Y``.
"""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.snapshots.cell_classifier import classify_blueprint_entry
from django_apps.asteroid_lab.snapshots.copy_json_coords import raw_x_to_export_column
from django_apps.asteroid_lab.snapshots.layout_fingerprint import layout_fingerprint_payload

# Re-export for ``snapshots.__init__`` (historical name).
layout_map_payload = layout_fingerprint_payload

_LAB_ENTRY_KEYS = frozenset({"X", "Y", "R", "T", "L", "Layer"})


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


def _strip_entry_for_compare(row: dict[str, Any]) -> dict[str, Any]:
    return {k: row[k] for k in _LAB_ENTRY_KEYS if k in row}


def _entries(decoded: dict[str, Any]) -> list[dict[str, Any]]:
    bp = decoded.get("BP")
    if not isinstance(bp, dict):
        return []
    raw = bp.get("Entries")
    if not isinstance(raw, list):
        return []
    return [e for e in raw if isinstance(e, dict)]


def _is_extractor_tile(t: str) -> bool:
    return t in ("Layout_FluidMiner", "Layout_ShapeMiner")


def _is_extension_tile(t: str) -> bool:
    return t in ("Layout_FluidMinerExtension", "Layout_ShapeMinerExtension")


def _is_transport_tile(t: str) -> bool:
    cell_kind, _tk = classify_blueprint_entry(t)
    return cell_kind in ("space_pipe", "space_belt")


def _filter_entries(
    rows: list[dict[str, Any]],
    *,
    include_transport: bool,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        t_raw = row.get("T")
        t = str(t_raw) if isinstance(t_raw, str) else ""
        if _is_extractor_tile(t) or _is_extension_tile(t):
            out.append(row)
            continue
        if include_transport and _is_transport_tile(t):
            out.append(row)
    return out


def _extractor_anchor_export_xy(rows: list[dict[str, Any]]) -> tuple[int, int] | None:
    """Anchor ``(export_x, raw_y)`` for the minimum extractor."""

    candidates: list[tuple[int, int]] = []
    for row in rows:
        t_raw = row.get("T")
        t = str(t_raw) if isinstance(t_raw, str) else ""
        if _is_extractor_tile(t):
            rx = _as_int(row.get("X"))
            ry = _as_int(row.get("Y"))
            candidates.append((raw_x_to_export_column(rx), ry))
    if not candidates:
        return None
    return min(candidates)


def _fallback_anchor_export_xy(rows: list[dict[str, Any]]) -> tuple[int, int]:
    if not rows:
        return (0, 0)
    dense_vals = [raw_x_to_export_column(_as_int(r.get("X"))) for r in rows]
    raw_y_vals = [_as_int(r.get("Y")) for r in rows]
    return (min(dense_vals), min(raw_y_vals))


def _normalized_signature(
    rows: list[dict[str, Any]],
    *,
    include_transport: bool,
) -> tuple[tuple[int, int, int, str], ...]:
    filtered = _filter_entries(rows, include_transport=include_transport)
    anchor = _extractor_anchor_export_xy(filtered)
    if anchor is None:
        odx, oy = _fallback_anchor_export_xy(filtered)
    else:
        odx, oy = anchor
    norm: list[tuple[int, int, int, str]] = []
    for row in filtered:
        clean = _strip_entry_for_compare(row)
        t_raw = clean.get("T")
        t = str(t_raw) if isinstance(t_raw, str) else ""
        rx = _as_int(clean.get("X"))
        rry = _as_int(clean.get("Y"))
        nx = raw_x_to_export_column(rx) - odx
        ny = rry - oy
        nr = _as_int(clean.get("R"))
        norm.append((nx, ny, nr, t))
    norm.sort()
    return tuple(norm)


def decoded_json_layout_equivalent(
    a: dict[str, Any],
    b: dict[str, Any],
    *,
    include_transport: bool,
) -> bool:
    """True if entries match up to translation on export-column X and raw Y."""

    sig_a = _normalized_signature(_entries(a), include_transport=include_transport)
    sig_b = _normalized_signature(_entries(b), include_transport=include_transport)
    return sig_a == sig_b


def copy_codes_layout_equivalent(
    code_a: str,
    code_b: str,
    *,
    include_transport: bool,
) -> bool:
    """Decode two v4 copy strings and compare layouts."""

    ra = decode_copy_string(code_a.strip().removesuffix("$")).root
    rb = decode_copy_string(code_b.strip().removesuffix("$")).root
    return decoded_json_layout_equivalent(ra, rb, include_transport=include_transport)


def copy_string_bytes_equivalent(code_a: str, code_b: str) -> bool:
    """Compare copy strings after whitespace strip (and optional trailing ``$``)."""

    def norm(s: str) -> str:
        t = "".join(s.split())
        return t.removesuffix("$")

    return norm(code_a) == norm(code_b)
