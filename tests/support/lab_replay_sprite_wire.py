"""Mirror Lab replay wire → sprite paint targets (parity with ``asteroid_miner_layout_lab.js``)."""

from __future__ import annotations

from collections.abc import Mapping

from django_apps.shapez_core.lab_sprite_path import (
    LAB_SPRITE_IDENTIFIER_ALIASES,
    resolve_sprite_static_relpath,
)

TERRAIN_KINDS = frozenset(
    {"asteroid_shape_field", "asteroid_fluid_field", "internal_void"},
)

NON_SPRITE_OVERLAY_CELL_KINDS = frozenset(
    {
        "candidate_transport_stub",
        "candidate_route_path",
        "route_path",
    },
)

ROUTE_OVERLAY_CELL_KINDS = frozenset(
    {"route_probe", "route_probe_path", "confirmed_route", "route_goal"},
)

CELL_KIND_STATIC_RELPATH = {
    "asteroid_fluid_field": "AsteroidField_Fluid.svg",
    "asteroid_shape_field": "AsteroidField_Shape.svg",
}

CELL_KIND_TO_IDENTIFIER = {
    "fluid_miner": "Layout_FluidMiner",
    "fluid_miner_extension": "Layout_FluidMinerExtension",
    "shape_miner": "Layout_ShapeMiner",
    "shape_miner_extension": "Layout_ShapeMinerExtension",
    "miner": "Layout_ShapeMiner",
    "extension": "Layout_ShapeMinerExtension",
}


def overlay_cell_kind(cell: Mapping[str, object]) -> str:
    ck = cell.get("cell_kind")
    if ck is not None and str(ck) != "":
        return str(ck)
    kind = cell.get("kind")
    if kind is not None and str(kind) != "":
        return str(kind)
    return ""


def normalize_replay_wire_cell(raw: Mapping[str, object]) -> dict[str, object]:
    tile_type = str(raw.get("tile_type") or raw.get("sprite_identifier") or "")
    return {
        "x": raw.get("x"),
        "y": raw.get("y"),
        "cell_kind": raw.get("kind") if raw.get("kind") is not None else raw.get("cell_kind"),
        "transport_kind": (
            raw.get("transport") if raw.get("transport") is not None else raw.get("transport_kind")
        ),
        "tile_type": tile_type,
        "sprite_identifier": str(raw.get("sprite_identifier") or tile_type),
        "rotation": raw.get("rotation"),
        "overlay_role": raw.get("overlay_role"),
    }


def _sprite_relpath_from_tile_type(tile_type: str) -> str | None:
    t = (tile_type or "").strip()
    if not t:
        return None
    t = LAB_SPRITE_IDENTIFIER_ALIASES.get(t, t)
    rel = resolve_sprite_static_relpath(t)
    if rel:
        return rel
    if t.startswith("SpaceBelt_"):
        return f"SpaceBelt/{t}.svg"
    if t.startswith("SpacePipe_"):
        return f"SpacePipe/{t}.svg"
    if t.startswith("Layout_"):
        return f"Miner/{t}.svg"
    return None


def _infer_transport_sprite_identifier(cell: Mapping[str, object]) -> str | None:
    ck = overlay_cell_kind(cell)
    if ck in {
        "miner",
        "extension",
        "shape_miner",
        "shape_miner_extension",
        "fluid_miner",
        "fluid_miner_extension",
    }:
        return None
    tk = str(cell.get("transport_kind") or cell.get("transport") or "")
    if tk in {"shape_belt", "space_belt"} or ck == "space_belt":
        return "SpaceBelt_Forward"
    if tk in {"fluid_pipe", "space_pipe"} or ck == "space_pipe":
        return "SpacePipe_Forward"
    return None


def is_non_sprite_overlay_cell(cell: Mapping[str, object]) -> bool:
    ck = overlay_cell_kind(cell)
    if not ck:
        return False
    return ck in NON_SPRITE_OVERLAY_CELL_KINDS


def lab_sprite_relpath_for_cell(cell: Mapping[str, object]) -> str | None:
    if not cell:
        return None
    ck = overlay_cell_kind(cell)
    if ck in {"candidate_miner", "miner"}:
        return None
    if is_non_sprite_overlay_cell(cell):
        return None
    if ck in ROUTE_OVERLAY_CELL_KINDS:
        return None
    static = CELL_KIND_STATIC_RELPATH.get(ck)
    if static:
        return static
    tile_key = str(cell.get("sprite_identifier") or cell.get("tile_type") or "")
    rel = _sprite_relpath_from_tile_type(tile_key)
    if not rel and ck:
        ident = CELL_KIND_TO_IDENTIFIER.get(ck)
        if ident:
            rel = _sprite_relpath_from_tile_type(ident)
    if not rel:
        inferred = _infer_transport_sprite_identifier(cell)
        if inferred:
            rel = _sprite_relpath_from_tile_type(inferred)
    return rel


def _cells_from_map_view(map_view: Mapping[str, object] | None) -> list[dict[str, object]]:
    if not isinstance(map_view, dict):
        return []
    out: list[dict[str, object]] = []
    for key in ("full_cells", "overlay_cells", "cell_delta"):
        rows = map_view.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                normalized = normalize_replay_wire_cell(row)
                out.append(normalized)
    return out


def full_map_cells_from_frame(frame: Mapping[str, object]) -> list[dict[str, object]]:
    map_view_raw = frame.get("map_view")
    map_view = map_view_raw if isinstance(map_view_raw, dict) else None
    from_mv = _cells_from_map_view(map_view)
    if from_mv:
        # ``fullMapCellsFromFrame`` prefers full_cells only when map_view has full_cells;
        # mirror that by taking full_cells first, else delta, else full_map list.
        map_view = frame.get("map_view")
        if isinstance(map_view, dict):
            full = map_view.get("full_cells")
            if isinstance(full, list) and full:
                return [normalize_replay_wire_cell(r) for r in full if isinstance(r, dict)]
            delta = map_view.get("cell_delta")
            if isinstance(delta, list) and delta:
                return [normalize_replay_wire_cell(r) for r in delta if isinstance(r, dict)]
    full_map = frame.get("full_map")
    if isinstance(full_map, list) and full_map:
        return [normalize_replay_wire_cell(r) for r in full_map if isinstance(r, dict)]
    overlay_json = cell_overlay_json_from_frame(frame)
    if isinstance(overlay_json, dict):
        cells = overlay_json.get("cells")
        if isinstance(cells, list) and cells:
            return [normalize_replay_wire_cell(r) for r in cells if isinstance(r, dict)]
    return []


def cell_overlay_json_from_frame(frame: Mapping[str, object]) -> dict[str, object] | None:
    top = frame.get("cell_overlay_json")
    if isinstance(top, dict):
        return top
    payload = frame.get("frame_payload")
    if isinstance(payload, dict):
        nested = payload.get("cell_overlay_json")
        if isinstance(nested, dict):
            return nested
    return None


def collect_overlay_paint_targets(overlay: Mapping[str, object]) -> list[dict[str, object]]:
    from django_apps.asteroid_lab.replay.replay_overlay_bucket_registry import (
        collect_overlay_cells_for_paint_target,
    )

    if not isinstance(overlay, dict):
        return []
    return [
        normalize_replay_wire_cell(row)
        for row in collect_overlay_cells_for_paint_target(dict(overlay))
    ]


def collect_frame_spatial_targets(frame: Mapping[str, object]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    out.extend(full_map_cells_from_frame(frame))
    map_view = frame.get("map_view")
    if isinstance(map_view, dict):
        for key in ("overlay_cells", "cell_delta"):
            rows = map_view.get(key)
            if not isinstance(rows, list):
                continue
            for row in rows:
                if isinstance(row, dict):
                    out.append(normalize_replay_wire_cell(row))
    diff = frame.get("diff")
    if isinstance(diff, dict):
        for role, key in (
            ("diff_removed", "removed"),
            ("diff_added", "added"),
        ):
            rows = diff.get(key)
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, dict):
                        out.append({**normalize_replay_wire_cell(row), "_role": role})
        changed = diff.get("changed")
        if isinstance(changed, list):
            for item in changed:
                if isinstance(item, dict) and isinstance(item.get("after"), dict):
                    out.append(
                        {**normalize_replay_wire_cell(item["after"]), "_role": "diff_changed"},
                    )
    overlay_json = cell_overlay_json_from_frame(frame)
    if isinstance(overlay_json, dict):
        out.extend(collect_overlay_paint_targets(overlay_json))
    return out


def _legacy_harvest_sprite_entries_for_frame(
    frame: Mapping[str, object],
) -> list[dict[str, object]]:
    """Harvest paint rows — parity reference only (Slice 5 quarantine)."""

    by_xy: dict[tuple[int, int], dict[str, object]] = {}
    for cell in collect_frame_spatial_targets(frame):
        x, y = cell.get("x"), cell.get("y")
        try:
            key = (int(x), int(y))
        except (TypeError, ValueError):
            continue
        rel = lab_sprite_relpath_for_cell(cell)
        prev = by_xy.get(key)
        if prev is None:
            by_xy[key] = {"cell": cell, "rel": rel}
            continue
        if rel and not prev.get("rel"):
            by_xy[key] = {"cell": cell, "rel": rel}
    sprites: list[dict[str, object]] = []
    for key, entry in by_xy.items():
        rel = entry.get("rel")
        if not rel:
            continue
        cell = entry["cell"]
        sprites.append(
            {
                "x": key[0],
                "y": key[1],
                "rel": rel,
                "rotation": int(cell.get("rotation") or 0),
            },
        )
    return sprites


def sprite_paint_entries_for_frame(frame: Mapping[str, object]) -> list[dict[str, object]]:
    """Return sprite paint rows ``{x, y, rel, rotation}`` (EffectiveCellView paint plan)."""

    from tests.support.lab_replay_paint_plan import sprite_entries_from_paint_plan_frame

    return sprite_entries_from_paint_plan_frame(frame)


def golden_transport_replay_frames() -> list[dict[str, object]]:
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        layer04_result_with_selection_for_golden,
        layer04_route_plan_with_transport_tiles_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    return list(
        build_solver_runtime_replay_frames(
            complete_map=golden_5x5_complete_map(),
            lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
            exterior_plan_wire=exterior_plan_wire_for_golden(),
            layer03=rim_bundle_candidate_set_with_observability_for_golden(),
            layer04=layer04_result_with_selection_for_golden(),
            layer05_route_plan=layer04_route_plan_with_transport_tiles_for_golden(),
        ),
    )


def overlay_fallback_fixture_frame() -> dict[str, object]:
    """``full_map`` + ``cell_overlay_json.cells`` pipe (Lab lookup parity)."""

    return {
        "frame_index": 0,
        "event_type": "fixture.overlay_fallback",
        "map_view": {
            "full_cells": [
                {
                    "x": 1,
                    "y": 0,
                    "kind": "fluid_miner",
                    "transport": "",
                    "tile_type": "Layout_ShapeMiner",
                    "rotation": 0,
                    "layer": 1,
                },
            ],
            "overlay_cells": [],
            "cell_delta": [],
        },
        "cell_overlay_json": {
            "cells": [
                {
                    "x": 2,
                    "y": 0,
                    "cell_kind": "space_pipe",
                    "tile_type": "SpacePipe_Forward",
                    "rotation": 1,
                    "layer": 2,
                },
            ],
        },
    }
