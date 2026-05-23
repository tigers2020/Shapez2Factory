"""Layout fingerprint: canonical JSON + SHA-256 (ORM-free)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from django_apps.asteroid_lab.snapshots.cell_classifier import classify_blueprint_entry
from django_apps.asteroid_lab.snapshots.copy_json_coords import entry_island_raw_coord

COORD_SYSTEM_ISLAND_BBOX_LEFT_BOTTOM = "island_bbox_left_bottom_raw_xy_v1"
_SCHEMA_LAYOUT = "asteroid-miner-layout-map.v2"
_SCHEMA_ABSOLUTE = "asteroid-miner-layout-absolute.v2"
COORD_ABSOLUTE_ISLAND = "island_raw_xy_v1"


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


def _fingerprint_kind(cell_kind: str) -> str | None:
    if cell_kind in ("shape_miner", "fluid_miner"):
        return "extractor"
    if cell_kind in ("shape_miner_extension", "fluid_miner_extension"):
        return "extension"
    return None


def _transport_label(cell_kind: str) -> str:
    if cell_kind.startswith("shape_"):
        return "shape"
    if cell_kind.startswith("fluid_"):
        return "fluid"
    return "none"


def _compact_json(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def layout_fingerprint_payload(decoded_json: dict[str, Any]) -> dict[str, Any]:
    """Canonical dict for bbox-normalized island layout (miners/extensions only).

    Uses copy JSON island-local ``X``/``Y`` via ``entry_island_raw_coord``.
    """

    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        bp = {}
    entries_raw = bp.get("Entries")
    entries: list[Any] = entries_raw if isinstance(entries_raw, list) else []

    staged: list[tuple[int, int, str, int, str]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        t_raw = item.get("T")
        tile_type = str(t_raw) if isinstance(t_raw, str) else ""
        cell_kind, _tk = classify_blueprint_entry(tile_type if tile_type else None)
        fk = _fingerprint_kind(cell_kind)
        if fk is None:
            continue
        island = entry_island_raw_coord(item)
        staged.append((island.x, island.y, fk, _as_int(item.get("R")), _transport_label(cell_kind)))

    rows: list[dict[str, Any]] = []
    if staged:
        min_x = min(s[0] for s in staged)
        min_y = min(s[1] for s in staged)
        max_nx = -1
        max_ny = -1
        for raw_x, raw_y, fk, rot, transport in staged:
            nx = raw_x - min_x
            ny = raw_y - min_y
            rows.append(
                {
                    "x": nx,
                    "y": ny,
                    "kind": fk,
                    "r": rot,
                    "transport": transport,
                }
            )
            max_nx = max(max_nx, nx)
            max_ny = max(max_ny, ny)
        bbox = {
            "island_width": 0 if max_nx < 0 else max_nx + 1,
            "island_height": 0 if max_ny < 0 else max_ny + 1,
        }
    else:
        bbox = {"island_width": 0, "island_height": 0}

    rows.sort(key=lambda row: (row["x"], row["y"], row["kind"], row["transport"], row["r"]))

    return {
        "schema": _SCHEMA_LAYOUT,
        "coord_system": COORD_SYSTEM_ISLAND_BBOX_LEFT_BOTTOM,
        "origin": "left_bottom",
        "axis": {"x": "left_positive", "y": "up_positive"},
        "bbox": bbox,
        "cells": rows,
    }


def layout_fingerprint_sha256(decoded_json: dict[str, Any]) -> str:
    payload = layout_fingerprint_payload(decoded_json)
    return hashlib.sha256(_compact_json(payload)).hexdigest()


def absolute_layout_fingerprint_payload(decoded_json: dict[str, Any]) -> dict[str, Any]:
    """Canonical dict using island-local x/y (translation-sensitive vs bbox-normalized layout)."""

    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        bp = {}
    entries_raw = bp.get("Entries")
    entries: list[Any] = entries_raw if isinstance(entries_raw, list) else []

    rows: list[dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        t_raw = item.get("T")
        tile_type = str(t_raw) if isinstance(t_raw, str) else ""
        cell_kind, _tk = classify_blueprint_entry(tile_type if tile_type else None)
        fk = _fingerprint_kind(cell_kind)
        if fk is None:
            continue
        island = entry_island_raw_coord(item)
        r = _as_int(item.get("R"))
        rows.append(
            {
                "x": island.x,
                "y": island.y,
                "kind": fk,
                "r": r,
                "transport": _transport_label(cell_kind),
            }
        )

    rows.sort(key=lambda row: (row["x"], row["y"], row["kind"], row["transport"], row["r"]))

    return {
        "schema": _SCHEMA_ABSOLUTE,
        "coord_system": COORD_ABSOLUTE_ISLAND,
        "cells": rows,
    }


def absolute_layout_fingerprint_sha256(decoded_json: dict[str, Any]) -> str:
    payload = absolute_layout_fingerprint_payload(decoded_json)
    return hashlib.sha256(_compact_json(payload)).hexdigest()


__all__ = [
    "COORD_SYSTEM_ISLAND_BBOX_LEFT_BOTTOM",
    "COORD_ABSOLUTE_ISLAND",
    "absolute_layout_fingerprint_payload",
    "absolute_layout_fingerprint_sha256",
    "layout_fingerprint_payload",
    "layout_fingerprint_sha256",
]
