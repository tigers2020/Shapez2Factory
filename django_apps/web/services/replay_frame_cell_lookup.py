"""Resolve one (x, y) cell payload from a serialized lab replay frame (read-only)."""

from __future__ import annotations

from typing import Any


def _xy_match(row: Any, x: int, y: int) -> bool:
    if not isinstance(row, dict):
        return False
    try:
        return int(row["x"]) == x and int(row["y"]) == y
    except (KeyError, TypeError, ValueError):
        return False


def _append_cells(out: list[dict[str, Any]], lst: Any) -> None:
    if not isinstance(lst, list):
        return
    for c in lst:
        if isinstance(c, dict):
            out.append(c)


def _push_from_blocks(out: list[dict[str, Any]], blocks: Any) -> None:
    if not isinstance(blocks, list):
        return
    for block in blocks:
        if not isinstance(block, dict):
            continue
        cells = block.get("cells")
        if isinstance(cells, list):
            _append_cells(out, cells)
        elif block.get("x") is not None and block.get("y") is not None:
            out.append(block)


def _collect_overlay_cells(overlay: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
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
            out.append(main)
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


def _cells_at_xy(cells: list[dict[str, Any]], x: int, y: int) -> list[dict[str, Any]]:
    return [c for c in cells if _xy_match(c, x, y)]


def _merge_layers(layers: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for d in layers:
        merged.update(d)
    return merged


def lookup_cell_in_serialized_frame(
    ser: dict[str, Any], x: int, y: int
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Match lab grid paint order: full_map + diff layers; else overlay-only."""

    sources: dict[str, Any] = {}

    full_map_raw = ser.get("full_map")
    if isinstance(full_map_raw, list) and len(full_map_raw) > 0:
        full_map_list: list[Any] = full_map_raw
        base_layers: list[dict[str, Any]] = []

        for row in full_map_list:
            if isinstance(row, dict) and _xy_match(row, x, y):
                sources["full_map"] = row
                base_layers.append(dict(row))
                break

        diff = ser.get("diff")
        if isinstance(diff, dict):
            for c in diff.get("removed") or []:
                if isinstance(c, dict) and _xy_match(c, x, y):
                    sources["diff_removed"] = c
                    base_layers.append(dict(c))
            for c in diff.get("added") or []:
                if isinstance(c, dict) and _xy_match(c, x, y):
                    sources["diff_added"] = c
                    base_layers.append(dict(c))
            for item in diff.get("changed") or []:
                if isinstance(item, dict):
                    after = item.get("after")
                    if isinstance(after, dict) and _xy_match(after, x, y):
                        sources["diff_changed_after"] = after
                        base_layers.append(dict(after))

        if not base_layers:
            return None, sources
        return _merge_layers(base_layers), sources

    ov2 = ser.get("cell_overlay_json")
    if isinstance(ov2, dict):
        overlay_cells = _collect_overlay_cells(ov2)
        matches = _cells_at_xy(overlay_cells, x, y)
        if matches:
            sources["overlay_cells_matched"] = len(matches)
            return _merge_layers([dict(m) for m in matches]), sources

    return None, sources
