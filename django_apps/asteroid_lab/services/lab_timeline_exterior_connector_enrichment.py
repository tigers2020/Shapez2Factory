"""Attach exterior connector plan wire to Lab replay frames (output-only)."""

from __future__ import annotations

import copy
from typing import Any

from django_apps.asteroid_lab.replay.persistent_connector_overlay_wire import (
    ConnectorRoleWire,
    PersistentConnectorOverlayWire,
)

METRICS_KEY = "exterior_connector_plan"
OVERLAY_ROLE = "planned_exterior_connector"


def _connector_coord_keys(plan_wire: dict[str, object]) -> set[tuple[int, int]]:
    keys: set[tuple[int, int]] = set()
    for row in planned_connector_overlays_from_wire(plan_wire):
        keys.add((int(row["x"]), int(row["y"])))
    return keys


def _overlay_without_connector_coord_duplicates(
    overlay: list[Any],
    connector_coords: set[tuple[int, int]],
) -> list[Any]:
    """Drop generic belt overlays on void coords reserved for white L2 markers."""

    out: list[Any] = []
    for row in overlay:
        if not isinstance(row, dict):
            out.append(row)
            continue
        if row.get("overlay_role") == OVERLAY_ROLE:
            out.append(row)
            continue
        x = row.get("x")
        y = row.get("y")
        if x is not None and y is not None and (int(x), int(y)) in connector_coords:
            continue
        out.append(row)
    return out


def enrich_lab_timeline_frames_with_exterior_connector_plan(
    frames: list[dict[str, Any]],
    *,
    plan_wire: dict[str, object] | None,
    l2_complete_frame_index: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, object] | None]:
    """Return enriched frames and optional frozen plan wire for track metrics.

    When *l2_complete_frame_index* is ``None``, no frame is enriched (append-stack:
    L2 markers only from ``exterior_transport.completed`` onward, never frame 0 default).
    """

    if plan_wire is None:
        return frames, None

    start = l2_complete_frame_index
    if start is None:
        return frames, None

    frozen_wire: dict[str, object] | None = None
    out: list[dict[str, Any]] = []

    for index, frame in enumerate(frames):
        fr_copy = copy.deepcopy(frame)
        if index < start:
            out.append(fr_copy)
            continue

        metrics = dict(fr_copy.get("metrics") or {})
        metrics.pop(METRICS_KEY, None)
        metrics[METRICS_KEY] = plan_wire
        if frozen_wire is None and index == start:
            frozen_wire = plan_wire

        map_view = fr_copy.get("map_view")
        if isinstance(map_view, dict):
            mv_copy = copy.deepcopy(map_view)
            connector_coords = _connector_coord_keys(plan_wire)
            overlay = mv_copy.get("overlay_cells")
            if not isinstance(overlay, list):
                overlay = []
            else:
                overlay = [
                    row
                    for row in overlay
                    if not (isinstance(row, dict) and row.get("overlay_role") == OVERLAY_ROLE)
                ]
                overlay = _overlay_without_connector_coord_duplicates(
                    overlay,
                    connector_coords,
                )
            for conn in planned_connector_overlays_from_wire(plan_wire):
                overlay.append(conn)
            mv_copy["overlay_cells"] = overlay
            fr_copy["map_view"] = mv_copy

        fr_copy["metrics"] = metrics
        out.append(fr_copy)

    return out, frozen_wire


def planned_connector_overlays_from_wire(
    plan_wire: dict[str, object],
) -> list[PersistentConnectorOverlayWire]:
    raw = plan_wire.get("planned_connectors")
    if not isinstance(raw, list):
        return []
    out: list[PersistentConnectorOverlayWire] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        void_coord = item.get("void_coord")
        if not isinstance(void_coord, dict):
            continue
        x = void_coord.get("x")
        y = void_coord.get("y")
        if x is None or y is None:
            continue
        role_raw = str(item.get("role") or "required").strip().lower()
        role: ConnectorRoleWire
        if role_raw == "spare":
            role = "spare"
        else:
            role = "required"
        out.append(
            PersistentConnectorOverlayWire(
                x=int(x),
                y=int(y),
                overlay_role=OVERLAY_ROLE,
                connector_role=role,
                tile_type=str(item.get("layout_t") or ""),
                rotation=int(item.get("rotation") or 0),
                connector_id=str(item.get("connector_id") or ""),
            )
        )
    return out


__all__ = [
    "METRICS_KEY",
    "OVERLAY_ROLE",
    "enrich_lab_timeline_frames_with_exterior_connector_plan",
    "planned_connector_overlays_from_wire",
]
