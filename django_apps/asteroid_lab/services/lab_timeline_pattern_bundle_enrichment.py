"""Attach pattern bundle highlight wire to Lab replay timeline frames (output-only)."""

from __future__ import annotations

import copy
from collections.abc import Mapping

from django_apps.asteroid_lab.replay.pattern_bundle_highlight import (
    METRICS_KEY,
    build_pattern_bundle_highlights_wire,
)
from django_apps.asteroid_lab.services.lab_timeline_rim_enrichment import frame_has_renderable_map
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def _pattern_bundle_wire_is_usable(metrics: Mapping[str, object]) -> bool:
    wire = metrics.get(METRICS_KEY)
    if not isinstance(wire, dict):
        return False
    bundles = wire.get("bundles")
    return isinstance(bundles, list) and len(bundles) > 0


def _cell_overlay_from_frame(frame: Mapping[str, object]) -> dict[str, object] | None:
    overlay = frame.get("cell_overlay_json")
    if isinstance(overlay, dict):
        return overlay
    payload = frame.get("frame_payload")
    if isinstance(payload, dict):
        nested = payload.get("cell_overlay_json")
        if isinstance(nested, dict):
            return nested
    return None


def _wire_from_equipment_bundles(bundles: list[object]) -> dict[str, object]:
    entries: list[tuple[str, frozenset[Coord], str | None]] = []
    for block in bundles:
        if not isinstance(block, dict):
            continue
        bundle_id = block.get("bundle_id")
        cells_json = block.get("cells_json")
        if not isinstance(cells_json, list):
            continue
        coords: set[Coord] = set()
        for cell in cells_json:
            if not isinstance(cell, dict):
                continue
            coords.add((int(cell["x"]), int(cell["y"])))
        if not coords:
            continue
        if bundle_id is not None:
            key = f"equipment:{int(bundle_id)}"
        else:
            key = f"equipment:{len(entries)}"
        entries.append((key, frozenset(coords), None))
    return build_pattern_bundle_highlights_wire(entries)


def enrich_lab_timeline_frames_with_pattern_bundle_highlights(
    frames: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Return frames with ``metrics.pattern_bundle_highlights`` when equipment bundles exist."""

    out: list[dict[str, object]] = []
    for frame in frames:
        fr_copy = copy.deepcopy(frame)
        metrics_raw = fr_copy.get("metrics")
        metrics: dict[str, object] = dict(metrics_raw) if isinstance(metrics_raw, dict) else {}
        if _pattern_bundle_wire_is_usable(metrics):
            fr_copy["metrics"] = metrics
            out.append(fr_copy)
            continue
        metrics.pop(METRICS_KEY, None)
        if not frame_has_renderable_map(fr_copy):
            fr_copy["metrics"] = metrics
            out.append(fr_copy)
            continue
        overlay = _cell_overlay_from_frame(fr_copy)
        bundles = overlay.get("equipment_bundles") if overlay else None
        if isinstance(bundles, list) and bundles:
            wire = _wire_from_equipment_bundles(bundles)
            if wire:
                metrics[METRICS_KEY] = wire
        fr_copy["metrics"] = metrics
        out.append(fr_copy)
    return out


__all__ = [
    "METRICS_KEY",
    "enrich_lab_timeline_frames_with_pattern_bundle_highlights",
]
