"""Resolve one (x, y) cell payload from a serialized lab replay frame (read-only)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.effective_cell_view import (
    effective_cell_to_wire,
    merge_effective_cell_view,
)
from django_apps.asteroid_lab.replay.effective_cell_wire import EffectiveCellWire
from django_apps.asteroid_lab.typing_boundary import JsonObject


def _row_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, (float, str)):
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    return 0


def _xy_match(row: object, x: int, y: int) -> bool:
    if not isinstance(row, dict):
        return False
    try:
        return _row_int(row["x"]) == x and _row_int(row["y"]) == y
    except KeyError:
        return False


def _append_cells(out: list[JsonObject], lst: object) -> None:
    if not isinstance(lst, list):
        return
    for c in lst:
        if isinstance(c, dict):
            out.append(dict(c))


def _push_from_blocks(out: list[JsonObject], blocks: object) -> None:
    if not isinstance(blocks, list):
        return
    for block in blocks:
        if not isinstance(block, dict):
            continue
        cells = block.get("cells")
        if isinstance(cells, list):
            _append_cells(out, cells)
        elif block.get("x") is not None and block.get("y") is not None:
            out.append(dict(block))


def _collect_overlay_cells(overlay: JsonObject) -> list[JsonObject]:
    out: list[JsonObject] = []
    _append_cells(out, overlay.get("cells"))
    _append_cells(out, overlay.get("equipment_cells"))
    _append_cells(out, overlay.get("equipment"))
    _append_cells(out, overlay.get("adjacent_transport"))
    _push_from_blocks(out, overlay.get("components"))
    _push_from_blocks(out, overlay.get("transport_components"))
    _append_cells(out, overlay.get("transport"))
    main = overlay.get("main_component_candidate")
    if isinstance(main, dict):
        cj = main.get("cells_json")
        if isinstance(cj, list):
            _append_cells(out, cj)
        elif main.get("x") is not None and main.get("y") is not None:
            out.append(dict(main))
    _append_cells(out, overlay.get("cleanup_candidate_cells"))

    handled = frozenset(
        {
            "cells",
            "equipment_cells",
            "equipment",
            "adjacent_transport",
            "components",
            "transport_components",
            "transport",
            "main_component_candidate",
            "cleanup_candidate_cells",
        }
    )
    for key, val in overlay.items():
        if key in handled or not isinstance(val, dict) or isinstance(val, list):
            continue
        cj = val.get("cells_json")
        if isinstance(cj, list):
            _append_cells(out, cj)
    return out


def _cells_at_xy(cells: list[JsonObject], x: int, y: int) -> list[JsonObject]:
    return [c for c in cells if _xy_match(c, x, y)]


def _merge_layers(layers: list[JsonObject]) -> JsonObject:
    merged: JsonObject = {}
    for d in layers:
        merged.update(d)
    return merged


def _bbox_blocks(ser: JsonObject) -> list[JsonObject]:
    blocks: list[JsonObject] = []
    for key in ("summary", "metric_snapshot_json"):
        block = ser.get(key)
        if isinstance(block, dict):
            bb = block.get("bbox")
            if isinstance(bb, dict):
                blocks.append(dict(bb))
    return blocks


def _island_bbox_from_serialized(ser: JsonObject) -> dict[str, int] | None:
    """Island-local min/max x/y from replay frame bbox (PR-F preferred)."""

    for bb in _bbox_blocks(ser):
        try:
            return {
                "min_x": _row_int(bb["min_x"]),
                "max_x": _row_int(bb["max_x"]),
                "min_y": _row_int(bb["min_y"]),
                "max_y": _row_int(bb["max_y"]),
            }
        except KeyError:
            continue
    return None


def _lab_empty_synthetic_cell(
    x: int,
    y: int,
) -> JsonObject:
    return {
        "x": int(x),
        "y": int(y),
        "layer": None,
        "rotation": 0,
        "cell_kind": "lab_empty",
        "transport_kind": "none",
        "tile_type": "",
        "_lab_synthetic": True,
    }


def _try_synthetic_lab_empty(
    ser: JsonObject, x: int, y: int
) -> tuple[JsonObject | None, dict[str, object]]:
    """Lab UI only: slot inside frame bbox with no persisted row (not solver input)."""

    island_bb = _island_bbox_from_serialized(ser)
    if island_bb is None:
        return None, {}
    if not (
        island_bb["min_x"] <= int(x) <= island_bb["max_x"]
        and island_bb["min_y"] <= int(y) <= island_bb["max_y"]
    ):
        return None, {}
    return (
        _lab_empty_synthetic_cell(x, y),
        {"lab_synthetic": "empty_island_cell"},
    )


def lookup_effective_cell_in_serialized_frame(
    ser: JsonObject, x: int, y: int
) -> tuple[EffectiveCellWire | None, dict[str, object]]:
    """Merge full_map / diff / overlay into one EffectiveCellView wire payload."""

    sources: dict[str, object] = {}
    full_cells: list[JsonObject] = []
    delta_cell: JsonObject | None = None
    overlay_matches: list[JsonObject] = []

    ov2 = ser.get("cell_overlay_json")
    if isinstance(ov2, dict):
        overlay_cells = _collect_overlay_cells(dict(ov2))
        overlay_matches = [dict(m) for m in _cells_at_xy(overlay_cells, x, y)]
        if overlay_matches:
            sources["overlay_cells_matched"] = len(overlay_matches)
            sources["overlay_cells"] = (
                overlay_matches if len(overlay_matches) > 1 else overlay_matches[0]
            )

    full_map_raw = ser.get("full_map")
    if isinstance(full_map_raw, list) and len(full_map_raw) > 0:
        for row in full_map_raw:
            if isinstance(row, dict) and _xy_match(row, x, y):
                sources["full_map"] = row
                full_cells.append(dict(row))

        diff = ser.get("diff")
        if isinstance(diff, dict):
            added = diff.get("added")
            if isinstance(added, list):
                for c in added:
                    if isinstance(c, dict) and _xy_match(c, x, y):
                        sources["diff_added"] = c
                        delta_cell = dict(c)
            changed = diff.get("changed")
            if isinstance(changed, list):
                for item in changed:
                    if isinstance(item, dict):
                        after = item.get("after")
                        if isinstance(after, dict) and _xy_match(after, x, y):
                            sources["diff_changed_after"] = after
                            delta_cell = dict(after)
            removed = diff.get("removed")
            if isinstance(removed, list):
                for c in removed:
                    if isinstance(c, dict) and _xy_match(c, x, y):
                        sources["diff_removed"] = c
                        if delta_cell is None:
                            delta_cell = dict(c)

    frame_index_raw = ser.get("frame_index")
    frame_index: int | None
    if frame_index_raw is None:
        frame_index = None
    elif isinstance(frame_index_raw, bool) or not isinstance(frame_index_raw, (int, str, float)):
        frame_index = None
    else:
        try:
            frame_index = int(frame_index_raw)
        except (TypeError, ValueError):
            frame_index = None

    view = None
    for full_cell in full_cells:
        view = merge_effective_cell_view(
            x=x,
            y=y,
            frame_index=frame_index,
            full_cell=full_cell,
            delta_cell=delta_cell,
            overlay_cells=overlay_matches or None,
        )
    if view is None and (delta_cell is not None or overlay_matches):
        view = merge_effective_cell_view(
            x=x,
            y=y,
            frame_index=frame_index,
            full_cell=None,
            delta_cell=delta_cell,
            overlay_cells=overlay_matches or None,
        )
    if view is not None:
        return effective_cell_to_wire(view), sources

    synthetic, syn_src = _try_synthetic_lab_empty(ser, x, y)
    if synthetic is not None:
        sources.update(syn_src)
        synthetic_view = merge_effective_cell_view(
            x=x,
            y=y,
            frame_index=frame_index,
            full_cell=synthetic,
        )
        if synthetic_view is not None:
            return effective_cell_to_wire(synthetic_view), sources

    return None, sources


def lookup_cell_in_serialized_frame(
    ser: JsonObject, x: int, y: int
) -> tuple[JsonObject | None, dict[str, object]]:
    """Deprecated flat merge; prefer ``lookup_effective_cell_in_serialized_frame``."""

    effective, sources = lookup_effective_cell_in_serialized_frame(ser, x, y)
    if effective is None:
        return None, sources
    occupant_kind = effective["occupant"]["kind"]
    if occupant_kind == "none" and effective["transport"]["kind"] != "none":
        occupant_kind = effective["transport"]["kind"]
    raw_kind: str | None = None
    raw_tile_type = ""
    for key in ("diff_removed", "diff_added", "diff_changed_after", "full_map"):
        block = sources.get(key)
        if isinstance(block, dict):
            raw_kind = str(block.get("cell_kind") or block.get("kind") or "") or raw_kind
            tile = block.get("tile_type") or block.get("sprite_identifier")
            if tile:
                raw_tile_type = str(tile)
    flat: JsonObject = {
        "x": effective["coord"]["x"],
        "y": effective["coord"]["y"],
        "layer": effective["coord"]["layer"],
        "cell_kind": raw_kind or occupant_kind,
        "transport_kind": effective["transport"]["kind"],
        "tile_type": raw_tile_type or effective["transport"]["tile_id"] or "",
        "rotation": effective["occupant"]["rotation"] or 0,
    }
    if sources.get("lab_synthetic") == "empty_island_cell":
        flat["_lab_synthetic"] = True
        flat["cell_kind"] = "lab_empty"
    return flat, sources
