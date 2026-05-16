"""Layout fingerprint: canonical JSON + SHA-256 (ORM-free)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from django_apps.asteroid_lab.snapshots.cell_classifier import classify_blueprint_entry
from django_apps.asteroid_lab.snapshots.server_coords import (
    COORD_SYSTEM_BBOX_RIGHT_BOTTOM,
    raw_x_to_dense_x,
)

_SCHEMA_LAYOUT = "asteroid-miner-layout-map.v1"
_SCHEMA_ABSOLUTE = "asteroid-miner-layout-absolute-dense.v1"
_COORD_ABSOLUTE = "absolute_dense_x_raw_y_v1"


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
    """Canonical dict for bbox-normalized server layout (miners/extensions only)."""

    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        bp = {}
    entries_raw = bp.get("Entries")
    entries: list[Any] = entries_raw if isinstance(entries_raw, list) else []

    rows: list[dict[str, Any]] = []
    max_sx = -1
    max_sy = -1
    for item in entries:
        if not isinstance(item, dict):
            continue
        t_raw = item.get("T")
        tile_type = str(t_raw) if isinstance(t_raw, str) else ""
        cell_kind, _tk = classify_blueprint_entry(tile_type if tile_type else None)
        fk = _fingerprint_kind(cell_kind)
        if fk is None:
            continue
        sx = item.get("server_x")
        sy = item.get("server_y")
        if not isinstance(sx, int) or not isinstance(sy, int):
            continue
        r = _as_int(item.get("R"))
        rows.append(
            {
                "server_x": sx,
                "server_y": sy,
                "kind": fk,
                "r": r,
                "transport": _transport_label(cell_kind),
            }
        )
        max_sx = max(max_sx, sx)
        max_sy = max(max_sy, sy)

    rows.sort(
        key=lambda row: (
            row["server_x"],
            row["server_y"],
            row["kind"],
            row["transport"],
            row["r"],
        )
    )

    return {
        "schema": _SCHEMA_LAYOUT,
        "coord_system": COORD_SYSTEM_BBOX_RIGHT_BOTTOM,
        "origin": "right_bottom",
        "axis": {"x": "left_positive", "y": "up_positive"},
        "bbox": {
            "server_width": 0 if max_sx < 0 else max_sx + 1,
            "server_height": 0 if max_sy < 0 else max_sy + 1,
        },
        "cells": rows,
    }


def layout_fingerprint_sha256(decoded_json: dict[str, Any]) -> str:
    payload = layout_fingerprint_payload(decoded_json)
    return hashlib.sha256(_compact_json(payload)).hexdigest()


def absolute_layout_fingerprint_payload(decoded_json: dict[str, Any]) -> dict[str, Any]:
    """Canonical dict using dense x + raw y (translation-sensitive vs bbox-normalized layout)."""

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
        x = _as_int(item.get("X"))
        y = _as_int(item.get("Y"))
        if x == 0:
            continue
        try:
            dense_x = raw_x_to_dense_x(x)
        except ValueError:
            continue
        r = _as_int(item.get("R"))
        rows.append(
            {
                "dense_x": dense_x,
                "raw_y": y,
                "kind": fk,
                "r": r,
                "transport": _transport_label(cell_kind),
            }
        )

    rows.sort(
        key=lambda row: (
            row["dense_x"],
            row["raw_y"],
            row["kind"],
            row["transport"],
            row["r"],
        )
    )

    return {
        "schema": _SCHEMA_ABSOLUTE,
        "coord_system": _COORD_ABSOLUTE,
        "cells": rows,
    }


def absolute_layout_fingerprint_sha256(decoded_json: dict[str, Any]) -> str:
    payload = absolute_layout_fingerprint_payload(decoded_json)
    return hashlib.sha256(_compact_json(payload)).hexdigest()


__all__ = [
    "absolute_layout_fingerprint_payload",
    "absolute_layout_fingerprint_sha256",
    "layout_fingerprint_payload",
    "layout_fingerprint_sha256",
]
