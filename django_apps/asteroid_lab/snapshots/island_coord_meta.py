"""Island-local coordinate metadata on persisted ``decoded_json`` (PR-F)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.snapshots.layout_fingerprint import (
    COORD_SYSTEM_ISLAND_BBOX_LEFT_BOTTOM,
)


def attach_island_coord_meta_to_decoded_json(decoded_json: dict[str, Any]) -> dict[str, Any]:
    """Record canonical coord system on decode persist without server dense attach."""

    meta = decoded_json.setdefault("_asteroid_lab_coord_system", {})
    if isinstance(meta, dict):
        meta["coord_system"] = COORD_SYSTEM_ISLAND_BBOX_LEFT_BOTTOM
        meta["frame"] = "island_raw"
        meta["x_rule"] = "copy_json_island_local_X"
        meta["y_rule"] = "copy_json_island_local_Y"
    return decoded_json


__all__ = ["attach_island_coord_meta_to_decoded_json"]
