"""Python mirror of LabPaintLayers resolver (parity authority for golden tests)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django_apps.asteroid_lab.replay.effective_cell_view import (
    merge_effective_cell_view,
)
from django_apps.asteroid_lab.replay.effective_cell_wire import effective_cell_to_wire
from django_apps.asteroid_lab.replay.replay_cell_index import cell_key
from django_apps.asteroid_lab.replay.replay_wire_read_sanitize import (
    sanitize_replay_wire_cell_for_read,
)
from django_apps.asteroid_lab.typing_boundary import JsonObject
from django_apps.shapez_core.lab_sprite_path import (
    LAB_SPRITE_IDENTIFIER_ALIASES,
    resolve_sprite_static_relpath,
)
from tests.support.lab_replay_sprite_wire import (
    CELL_KIND_STATIC_RELPATH,
    cell_overlay_json_from_frame,
)

# Mirror ``lab_replay_paint_plan.js`` occupant identifier map.
CELL_KIND_TO_IDENTIFIER = {
    "fluid_miner": "Layout_FluidMiner",
    "fluid_miner_extension": "Layout_FluidMinerExtension",
    "shape_miner": "Layout_ShapeMiner",
    "shape_miner_extension": "Layout_ShapeMinerExtension",
    "miner": "Layout_ShapeMiner",
    "extension": "Layout_ShapeMinerExtension",
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

# Mirror ``lab_replay_canvas_terrain.js`` TERRAIN_FILL defaults.
BACKGROUND_FILL = "rgb(2, 6, 23)"
VOID_FILL = "rgba(74, 4, 78, 0.72)"

VOID_TERRAIN_KINDS = frozenset({"internal_void", "void"})
TRANSPORT_KINDS = frozenset({"space_belt", "space_pipe"})
_NONE_KINDS = frozenset({"", "none"})

CANDIDATE_RING_STROKE = "rgba(244,114,182,0.9)"

DOM_CANDIDATE_MINER_RING = "lab-overlay-candidate-miner-ring relative"
DOM_CANDIDATE_MINER_FILL = "lab-overlay-candidate-miner relative"


def _wire_section(view: Mapping[str, object], key: str) -> dict[str, object]:
    section = view.get(key)
    return dict(section) if isinstance(section, Mapping) else {}


def _kind_str(section: Mapping[str, object], field: str = "kind") -> str:
    raw = section.get(field)
    return str(raw).strip() if raw is not None else ""


def _rotation(section: Mapping[str, object]) -> int:
    raw = section.get("rotation")
    if raw is None:
        return 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def _candidate_miner_occupant(output_transport_kind: str, rotation: int) -> dict[str, object]:
    if output_transport_kind == "space_pipe":
        rel = "Miner/Layout_FluidMiner.svg"
    else:
        rel = "Miner/Layout_ShapeMiner.svg"
    return {"rel": rel, "rotation": rotation}


def _committed_occupant_sprite(occupant_kind: str, output_transport_kind: str) -> str | None:
    if occupant_kind == "committed_miner":
        ident = (
            "Layout_FluidMiner"
            if output_transport_kind == "space_pipe"
            else "Layout_ShapeMiner"
        )
        return _sprite_relpath_from_tile_type(ident)
    if occupant_kind == "extension":
        ident = (
            "Layout_FluidMinerExtension"
            if output_transport_kind == "space_pipe"
            else "Layout_ShapeMinerExtension"
        )
        return _sprite_relpath_from_tile_type(ident)
    ident = CELL_KIND_TO_IDENTIFIER.get(occupant_kind)
    if ident:
        return _sprite_relpath_from_tile_type(ident)
    return None


def _resolve_occupant(
    view: Mapping[str, object],
) -> tuple[dict[str, object] | None, list[dict[str, object]]]:
    occupant = _wire_section(view, "occupant")
    output = _wire_section(view, "output")
    kind = _kind_str(occupant)
    if kind in _NONE_KINDS:
        return None, []

    rotation = _rotation(occupant)
    output_transport_kind = _kind_str(output, "transport_kind") or "none"
    chrome: list[dict[str, object]] = []

    if kind == "candidate_miner":
        chrome.append({"kind": "candidate_ring", "stroke_only": True})
        return _candidate_miner_occupant(output_transport_kind, rotation), chrome

    rel = _committed_occupant_sprite(kind, output_transport_kind)
    if rel:
        return {"rel": rel, "rotation": rotation}, chrome
    return None, chrome


def _rotation_from_overlay_sources(view: Mapping[str, object]) -> int:
    sources = view.get("sources")
    if not isinstance(sources, Mapping):
        return 0
    overlays = sources.get("overlay_cells")
    if overlays is None:
        return 0
    rows = overlays if isinstance(overlays, list) else [overlays]
    for row in rows:
        if isinstance(row, Mapping):
            rot = _rotation(row)
            if rot:
                return rot
    return 0


def _resolve_transport(
    view: Mapping[str, object],
    *,
    occupant_kind: str,
) -> dict[str, object] | None:
    if occupant_kind == "candidate_miner":
        return None

    transport = _wire_section(view, "transport")
    transport_kind = _kind_str(transport)
    if transport_kind not in TRANSPORT_KINDS:
        return None

    tile_id = transport.get("tile_id")
    if not tile_id or not str(tile_id).strip():
        return None

    rel = _sprite_relpath_from_tile_type(str(tile_id))
    if not rel:
        return None

    occupant = _wire_section(view, "occupant")
    rotation = _rotation(occupant)
    if _kind_str(occupant) in _NONE_KINDS:
        overlay_rotation = _rotation_from_overlay_sources(view)
        if overlay_rotation:
            rotation = overlay_rotation
    return {"rel": rel, "rotation": rotation}


def _resolve_terrain(
    view: Mapping[str, object],
    *,
    has_sprite: bool,
) -> dict[str, object] | None:
    terrain = _wire_section(view, "terrain")
    kind = _kind_str(terrain) or "empty"

    static_rel = CELL_KIND_STATIC_RELPATH.get(kind)
    if static_rel:
        return {"mode": "field_sprite", "rel": static_rel}

    if kind in VOID_TERRAIN_KINDS:
        return {"mode": "void_fill", "fill": VOID_FILL}

    if not has_sprite:
        return {"mode": "background_fill", "fill": BACKGROUND_FILL}

    return None


def lab_paint_layers_from_view(view: Mapping[str, object]) -> dict[str, Any]:
    """Resolve EffectiveCellWire → LabPaintLayers visual slots."""

    occupant, chrome = _resolve_occupant(view)
    occupant_kind = _kind_str(_wire_section(view, "occupant")) or "none"
    transport = _resolve_transport(view, occupant_kind=occupant_kind)
    has_sprite = occupant is not None or transport is not None
    terrain = _resolve_terrain(view, has_sprite=has_sprite)

    if terrain is not None and has_sprite and terrain.get("mode") == "background_fill":
        terrain = None

    return {
        "terrain": terrain,
        "occupant": occupant,
        "transport": transport,
        "chrome": chrome,
    }


def _row_int(value: object, *, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, (float, str)):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    return default


def _cell_coord(row: Mapping[str, object]) -> tuple[int, int, int]:
    return (
        _row_int(row.get("x")),
        _row_int(row.get("y")),
        _row_int(row.get("layer")),
    )


def _rows_at_coord(
    rows: list[JsonObject] | None,
    x: int,
    y: int,
    layer: int,
) -> list[JsonObject]:
    if not rows:
        return []
    return [row for row in rows if _cell_coord(row) == (x, y, layer)]


def _first_row_at_coord(
    rows: list[JsonObject] | None,
    x: int,
    y: int,
    layer: int,
) -> JsonObject | None:
    matches = _rows_at_coord(rows, x, y, layer)
    return matches[0] if matches else None


def _collect_coord_universe(
    map_view: Mapping[str, object],
    *,
    extra_rows: list[JsonObject] | None = None,
) -> set[tuple[int, int, int]]:
    coords: set[tuple[int, int, int]] = set()
    for key in ("full_cells", "overlay_cells", "cell_delta"):
        rows = map_view.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, Mapping):
                coords.add(_cell_coord(row))
    if extra_rows:
        for row in extra_rows:
            if isinstance(row, Mapping):
                coords.add(_cell_coord(row))
    return coords


def _overlay_json_rows_from_frame(frame: Mapping[str, object]) -> list[JsonObject]:
    """Paint-target rows from ``cell_overlay_json`` (sparse overlay frame parity)."""

    overlay = cell_overlay_json_from_frame(frame)
    if not overlay:
        return []
    from django_apps.asteroid_lab.replay.replay_overlay_bucket_registry import (
        collect_overlay_cells_for_paint_target,
    )

    return [
        dict(row)
        for row in collect_overlay_cells_for_paint_target(dict(overlay))
        if isinstance(row, Mapping)
    ]


def build_effective_cell_view_index(
    frame: Mapping[str, object],
    *,
    carry_layout_snapshot: Mapping[str, object] | None = None,
) -> dict[str, dict[str, object]]:
    """Build per-frame effective-cell wire index keyed by ``cell_key(x, y, layer)``.

    Collects the visible coordinate universe from ``map_view.full_cells``,
    ``overlay_cells``, ``cell_delta``, and paint-target ``cell_overlay_json``
    rows. For each coordinate, sanitizes all merge inputs, merges via
    ``merge_effective_cell_view``, and serializes with ``effective_cell_to_wire``.

    ``carry_layout_snapshot`` is reserved for Slice 3 layout-carry expansion;
    ignored when ``None``.
    """

    del carry_layout_snapshot  # Slice 3: sparse/delta frame carry hook

    map_view_raw = frame.get("map_view")
    if not isinstance(map_view_raw, Mapping):
        return {}

    map_view = dict(map_view_raw)
    full_rows = [
        dict(row)
        for row in map_view.get("full_cells", [])
        if isinstance(row, Mapping)
    ]
    overlay_rows = [
        dict(row)
        for row in map_view.get("overlay_cells", [])
        if isinstance(row, Mapping)
    ]
    delta_rows = [
        dict(row)
        for row in map_view.get("cell_delta", [])
        if isinstance(row, Mapping)
    ]
    overlay_json_rows = _overlay_json_rows_from_frame(frame)

    frame_index_raw = frame.get("frame_index")
    frame_index: int | None
    if frame_index_raw is None:
        frame_index = None
    else:
        try:
            frame_index = int(frame_index_raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            frame_index = None

    index: dict[str, dict[str, object]] = {}
    for x, y, layer in sorted(
        _collect_coord_universe(map_view, extra_rows=overlay_json_rows),
    ):
        full_cell = _first_row_at_coord(full_rows, x, y, layer)
        delta_cell = _first_row_at_coord(delta_rows, x, y, layer)
        overlay_cells = _rows_at_coord(overlay_rows, x, y, layer)
        overlay_cells.extend(_rows_at_coord(overlay_json_rows, x, y, layer))
        if not overlay_cells:
            overlay_cells = None

        sanitized_full = (
            sanitize_replay_wire_cell_for_read(full_cell) if full_cell is not None else None
        )
        sanitized_delta = (
            sanitize_replay_wire_cell_for_read(delta_cell) if delta_cell is not None else None
        )
        sanitized_overlays = (
            [sanitize_replay_wire_cell_for_read(row) for row in overlay_cells]
            if overlay_cells
            else None
        )

        view = merge_effective_cell_view(
            x=x,
            y=y,
            frame_index=frame_index,
            full_cell=sanitized_full,
            delta_cell=sanitized_delta,
            overlay_cells=sanitized_overlays,
        )
        if view is None:
            continue
        index[cell_key(x, y, layer)] = dict(effective_cell_to_wire(view))

    return index


def _is_rgba_fill(value: object) -> bool:
    return isinstance(value, str) and value.strip().lower().startswith("rgba(")


def _sprite_plan_entry(grid_idx: int, rel: str, rotation: int) -> dict[str, object]:
    return {"idx": grid_idx, "rel": rel, "rotation": rotation}


def canvas_plan_from_paint_layers(
    layers: Mapping[str, object],
    *,
    grid_idx: int = 0,
) -> dict[str, list[dict[str, object]]]:
    """Convert LabPaintLayers for one cell into canvas ``{sprites, overlays}`` plan."""

    sprites: list[dict[str, object]] = []

    terrain = layers.get("terrain")
    if isinstance(terrain, Mapping) and terrain.get("mode") == "field_sprite":
        rel = terrain.get("rel")
        if rel:
            sprites.append(_sprite_plan_entry(grid_idx, str(rel), 0))

    occupant = layers.get("occupant")
    if isinstance(occupant, Mapping) and occupant.get("rel"):
        sprites.append(
            _sprite_plan_entry(grid_idx, str(occupant["rel"]), _rotation(occupant))
        )

    transport = layers.get("transport")
    if isinstance(transport, Mapping) and transport.get("rel"):
        sprites.append(
            _sprite_plan_entry(grid_idx, str(transport["rel"]), _rotation(transport))
        )

    overlays: list[dict[str, object]] = []
    chrome = layers.get("chrome")
    if isinstance(chrome, list):
        for entry in chrome:
            if not isinstance(entry, Mapping):
                continue
            kind = _kind_str(entry)
            if kind == "candidate_ring":
                overlays.append(
                    {
                        "idx": grid_idx,
                        "kind": "candidate_ring",
                        "stroke": CANDIDATE_RING_STROKE,
                        "fill": None,
                    }
                )

    if sprites:
        overlays = [
            overlay
            for overlay in overlays
            if not _is_rgba_fill(overlay.get("fill"))
        ]

    return {"sprites": sprites, "overlays": overlays}


def _layers_have_sprite(layers: Mapping[str, object]) -> bool:
    """Tone anti-fade: occupant OR transport sprite blocks full-fill."""
    for slot in ("occupant", "transport"):
        entry = layers.get(slot)
        if isinstance(entry, Mapping) and entry.get("rel"):
            return True
    return False


def _index_spatial_rank(frame: Mapping[str, object]) -> dict[str, int]:
    """Harvest ``collect_frame_spatial_targets`` order for index keys (parity collapse)."""

    from django_apps.asteroid_lab.replay.replay_cell_index import cell_key
    from tests.support.lab_replay_sprite_wire import collect_frame_spatial_targets

    rank: dict[str, int] = {}
    for i, cell in enumerate(collect_frame_spatial_targets(frame)):
        if not isinstance(cell, Mapping):
            continue
        try:
            x = int(cell["x"])  # type: ignore[arg-type]
            y = int(cell["y"])  # type: ignore[arg-type]
        except (TypeError, ValueError, KeyError):
            continue
        layer_raw = cell.get("layer")
        layer = int(layer_raw) if layer_raw is not None else 0
        rank.setdefault(cell_key(x, y, layer), i)
    return rank


def sprite_entries_from_paint_plan_frame(
    frame: Mapping[str, object],
) -> list[dict[str, object]]:
    """Sprite paint rows ``{x, y, rel, rotation}`` via EffectiveCellView paint plan."""

    index = build_effective_cell_view_index(frame)
    rank = _index_spatial_rank(frame)
    ordered_keys = sorted(index.keys(), key=lambda k: (rank.get(k, 10**9), k))

    by_xy: dict[tuple[int, int], dict[str, object]] = {}
    for key in ordered_keys:
        view = index[key]
        coord = view.get("coord")
        if not isinstance(coord, Mapping):
            continue
        x = _row_int(coord.get("x"))
        y = _row_int(coord.get("y"))
        occupant_kind = _kind_str(_wire_section(view, "occupant")) or "none"
        layers = lab_paint_layers_from_view(view)
        plan = canvas_plan_from_paint_layers(layers)
        occupant = layers.get("occupant")

        for entry in plan.get("sprites", []):
            if not isinstance(entry, Mapping):
                continue
            rel = entry.get("rel")
            if not rel:
                continue
            if occupant_kind == "candidate_miner" and isinstance(occupant, Mapping):
                if str(rel) == str(occupant.get("rel")):
                    continue
            row = {
                "x": x,
                "y": y,
                "rel": str(rel),
                "rotation": _rotation(entry),
            }
            key_xy = (x, y)
            prev = by_xy.get(key_xy)
            if prev is None:
                by_xy[key_xy] = row
            elif row["rel"] and not prev.get("rel"):
                by_xy[key_xy] = row

    return [entry for entry in by_xy.values() if entry.get("rel")]


def dom_plan_from_paint_layers(
    layers: Mapping[str, object],
    *,
    overlay_kind: str = "",
) -> dict[str, object]:
    occupant = layers.get("occupant")
    chrome = layers.get("chrome")
    has_sprite = _layers_have_sprite(layers)
    has_candidate_ring = isinstance(chrome, list) and any(
        isinstance(c, Mapping) and c.get("kind") == "candidate_ring" for c in chrome
    )

    sprite_rel: str | None = None
    sprite_rotation = 0
    if isinstance(occupant, Mapping) and occupant.get("rel"):
        sprite_rel = str(occupant["rel"])
        sprite_rotation = _rotation(occupant)

    tone_classes = ""
    if has_candidate_ring:
        tone_classes = (
            DOM_CANDIDATE_MINER_RING if has_sprite else DOM_CANDIDATE_MINER_FILL
        )
    elif overlay_kind == "candidate_miner" and not has_sprite:
        tone_classes = DOM_CANDIDATE_MINER_FILL

    return {
        "tone_classes": tone_classes,
        "sprite_rel": sprite_rel,
        "sprite_rotation": sprite_rotation,
        "candidate_observation": has_candidate_ring or overlay_kind == "candidate_miner",
        "skip_full_fill": has_sprite,
    }


__all__ = [
    "BACKGROUND_FILL",
    "CANDIDATE_RING_STROKE",
    "DOM_CANDIDATE_MINER_FILL",
    "DOM_CANDIDATE_MINER_RING",
    "VOID_FILL",
    "build_effective_cell_view_index",
    "canvas_plan_from_paint_layers",
    "dom_plan_from_paint_layers",
    "lab_paint_layers_from_view",
    "sprite_entries_from_paint_plan_frame",
]
