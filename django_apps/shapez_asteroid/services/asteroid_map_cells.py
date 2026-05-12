"""BBox query and validation for asteroid map cells (DB-backed world status)."""

from __future__ import annotations

from typing import Any

from django.apps import apps
from django.http import QueryDict

# Max inclusive span per axis (inclusive range length).
_MAX_AXIS_SPAN = 256

# Slug used when no DB row exists for a coordinate inside the loaded bbox.
DEFAULT_VOID_SLUG = "void"


def void_kind_label() -> tuple[str, str]:
    """Return (slug, label) for void; fallback if DB not migrated or row missing."""

    AsteroidCellStatusKind = apps.get_model("shapez_asteroid", "AsteroidCellStatusKind")
    row = (
        AsteroidCellStatusKind.objects.filter(slug=DEFAULT_VOID_SLUG)
        .values_list("slug", "label")
        .first()
    )
    if row:
        return str(row[0]), str(row[1])
    return DEFAULT_VOID_SLUG, "void"


def parse_bbox(query: QueryDict) -> tuple[dict[str, Any] | None, tuple[int, int, int, int] | None]:
    """Return (error_json, bbox) where error_json is set on validation failure."""

    keys = ("x_min", "x_max", "y_min", "y_max")
    raw: dict[str, str | None] = {k: query.get(k) for k in keys}
    if any(raw[k] is None or str(raw[k]).strip() == "" for k in keys):
        return ({"ok": False, "error": "missing x_min, x_max, y_min, or y_max"}, None)
    try:
        x_min = int(str(raw["x_min"]))
        x_max = int(str(raw["x_max"]))
        y_min = int(str(raw["y_min"]))
        y_max = int(str(raw["y_max"]))
    except ValueError:
        return ({"ok": False, "error": "bounds must be integers"}, None)

    if x_min > x_max or y_min > y_max:
        return ({"ok": False, "error": "min must be <= max for each axis"}, None)

    if x_max - x_min + 1 > _MAX_AXIS_SPAN or y_max - y_min + 1 > _MAX_AXIS_SPAN:
        return ({"ok": False, "error": "bbox span too large"}, None)

    if x_min <= 0 <= x_max:
        return ({"ok": False, "error": "bbox must not include x=0"}, None)

    return (None, (x_min, x_max, y_min, y_max))


def list_map_cells_json(x_min: int, x_max: int, y_min: int, y_max: int) -> dict[str, Any]:
    """Serializable payload for map-cells API."""

    void_slug, void_label = void_kind_label()
    AsteroidMapCell = apps.get_model("shapez_asteroid", "AsteroidMapCell")

    qs = (
        AsteroidMapCell.objects.filter(x__gte=x_min, x__lte=x_max, y__gte=y_min, y__lte=y_max)
        .select_related("kind")
        .order_by("y", "x")
    )
    cells = [{"x": c.x, "y": c.y, "slug": c.kind.slug, "label": c.kind.label} for c in qs]
    return {
        "ok": True,
        "cells": cells,
        "void_slug": void_slug,
        "void_label": void_label,
    }
