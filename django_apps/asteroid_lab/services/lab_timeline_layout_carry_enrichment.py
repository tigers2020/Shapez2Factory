"""Carry rich layout overlays onto sparse tail replay frames (L5/L6 milestones)."""

from __future__ import annotations

import copy

from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
    OVERLAY_ROLE as PLANNED_EXTERIOR_CONNECTOR_ROLE,
)

_LAYOUT_OVERLAY_ROLES = frozenset(
    {
        PLANNED_EXTERIOR_CONNECTOR_ROLE,
        "committed_rim_equipment",
        "committed_inner_fill",
        "shape_miner",
        "shape_miner_extension",
        "fluid_miner",
        "fluid_miner_extension",
        "space_belt",
        "space_pipe",
        "route_probe",
        "route_probe_path",
        "confirmed_route",
        "route_goal",
        "candidate_transport_stub",
        "candidate_route_path",
        "route_path",
    }
)


def _overlay_row_role(row: object) -> str:
    if not isinstance(row, dict):
        return ""
    role = row.get("overlay_role")
    if isinstance(role, str) and role.strip():
        return role.strip()
    kind = row.get("kind")
    if isinstance(kind, str) and kind.strip():
        return kind.strip()
    return ""


def overlay_cells_are_layout_sparse(overlay: list[object]) -> bool:
    """True when a frame has no equipment/routes (connectors-only or empty)."""

    if not overlay:
        return True
    for row in overlay:
        role = _overlay_row_role(row)
        if role and role not in {PLANNED_EXTERIOR_CONNECTOR_ROLE}:
            if role in _LAYOUT_OVERLAY_ROLES or role.startswith("candidate_"):
                return False
            tile_type = row.get("tile_type") if isinstance(row, dict) else None
            if isinstance(tile_type, str) and tile_type.strip():
                return False
    return True


def enrich_lab_timeline_frames_with_carried_layout_overlays(
    frames: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Copy the latest rich ``overlay_cells`` onto sparse tail milestone frames."""

    last_layout_overlays: list[object] | None = None
    out: list[dict[str, object]] = []

    for frame in frames:
        fr_copy = copy.deepcopy(frame)
        map_view = fr_copy.get("map_view")
        if isinstance(map_view, dict):
            overlay_raw = map_view.get("overlay_cells")
            overlay = list(overlay_raw) if isinstance(overlay_raw, list) else []
            if not overlay_cells_are_layout_sparse(overlay):
                last_layout_overlays = overlay
            elif last_layout_overlays is not None:
                map_view = dict(map_view)
                map_view["overlay_cells"] = copy.deepcopy(last_layout_overlays)
                fr_copy["map_view"] = map_view
        out.append(fr_copy)

    return out


__all__ = [
    "enrich_lab_timeline_frames_with_carried_layout_overlays",
    "overlay_cells_are_layout_sparse",
]
