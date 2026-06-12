"""Layout/bbox coordinate helpers — mirrors lab.js spatial universe (not paint authority)."""

from __future__ import annotations

from collections.abc import Mapping

from tests.support.lab_replay_sprite_wire import (
    cell_overlay_json_from_frame,
    collect_frame_spatial_targets,
    collect_overlay_paint_targets,
    full_map_cells_from_frame,
    normalize_replay_wire_cell,
)

REPLAY_GRID_EDGE_PADDING = 5


def _visual_col(x: object) -> int | None:
    try:
        xi = int(x)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return xi


def _cells_from_map_view_full_cells(map_view: Mapping[str, object]) -> list[dict[str, object]]:
    full = map_view.get("full_cells")
    if not isinstance(full, list) or not full:
        return []
    return [normalize_replay_wire_cell(row) for row in full if isinstance(row, dict)]


def _overlay_cells_from_map_view(map_view: Mapping[str, object]) -> list[dict[str, object]]:
    rows = map_view.get("overlay_cells")
    if not isinstance(rows, list):
        return []
    return [normalize_replay_wire_cell(row) for row in rows if isinstance(row, dict)]


def _cell_delta_from_map_view(map_view: Mapping[str, object]) -> list[dict[str, object]]:
    rows = map_view.get("cell_delta")
    if not isinstance(rows, list):
        return []
    return [normalize_replay_wire_cell(row) for row in rows if isinstance(row, dict)]


def _diff_paint_cells(frame: Mapping[str, object]) -> list[dict[str, object]]:
    diff = frame.get("diff")
    if not isinstance(diff, dict):
        payload = frame.get("frame_payload")
        if isinstance(payload, dict) and isinstance(payload.get("diff"), dict):
            diff = payload["diff"]
    if not isinstance(diff, dict):
        return []
    out: list[dict[str, object]] = []
    for key in ("removed", "added"):
        rows = diff.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                out.append(normalize_replay_wire_cell(row))
    changed = diff.get("changed")
    if isinstance(changed, list):
        for item in changed:
            if isinstance(item, dict) and isinstance(item.get("after"), dict):
                out.append(normalize_replay_wire_cell(item["after"]))
    return out


def collect_replay_spatial_coords_for_layout(
    frame: Mapping[str, object],
) -> list[dict[str, object]]:
    """Coord-only layout universe — superset of legacy harvest spatial targets."""
    out: list[dict[str, object]] = []
    out.extend(full_map_cells_from_frame(frame))
    map_view = frame.get("map_view")
    if isinstance(map_view, dict):
        out.extend(_cells_from_map_view_full_cells(map_view))
        out.extend(_overlay_cells_from_map_view(map_view))
        out.extend(_cell_delta_from_map_view(map_view))
    out.extend(_diff_paint_cells(frame))
    overlay_json = cell_overlay_json_from_frame(frame)
    if isinstance(overlay_json, dict):
        out.extend(collect_overlay_paint_targets(overlay_json))
    return out


def _coord_keys(cells: list[dict[str, object]]) -> set[tuple[int, int]]:
    keys: set[tuple[int, int]] = set()
    for cell in cells:
        d = _visual_col(cell.get("x"))
        try:
            yi = int(cell.get("y"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if d is None:
            continue
        keys.add((d, yi))
    return keys


def compute_replay_grid_layout_from_frames(
    frames: list[Mapping[str, object]],
    *,
    collect_coords=collect_replay_spatial_coords_for_layout,
) -> dict[str, int]:
    """Mirror ``computeReplayGridLayout`` in asteroid_miner_layout_lab.js."""
    min_d = max_d = min_r = max_r = 0
    any_cell = False
    min_d_f = float("inf")
    max_d_f = float("-inf")
    min_r_f = float("inf")
    max_r_f = float("-inf")
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        for cell in collect_coords(frame):
            d = _visual_col(cell.get("x"))
            try:
                yi = int(cell.get("y"))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
            if d is None:
                continue
            any_cell = True
            min_d_f = min(min_d_f, d)
            max_d_f = max(max_d_f, d)
            min_r_f = min(min_r_f, yi)
            max_r_f = max(max_r_f, yi)
    if not any_cell:
        min_d = max_d = min_r = max_r = 0
    else:
        min_d = int(min_d_f)
        max_d = int(max_d_f)
        min_r = int(min_r_f)
        max_r = int(max_r_f)
    core_half_x = max(max(0, -min_d), max(0, max_d), 1)
    core_half_y = max(max(0, -min_r), max(0, max_r), 1)
    half_x = core_half_x + REPLAY_GRID_EDGE_PADDING
    half_y = core_half_y + REPLAY_GRID_EDGE_PADDING
    return {
        "minD": -half_x,
        "maxD": half_x,
        "minR": -half_y,
        "maxR": half_y,
        "gridW": 2 * half_x + 1,
        "gridH": 2 * half_y + 1,
    }


def harvest_spatial_coord_keys(frame: Mapping[str, object]) -> set[tuple[int, int]]:
    return _coord_keys(collect_frame_spatial_targets(frame))


def layout_spatial_coord_keys(frame: Mapping[str, object]) -> set[tuple[int, int]]:
    return _coord_keys(collect_replay_spatial_coords_for_layout(frame))
