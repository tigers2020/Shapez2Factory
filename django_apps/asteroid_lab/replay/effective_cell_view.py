"""EffectiveCellView — merged terrain / occupant / transport / output for Lab cell detail UI."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from django_apps.asteroid_lab.replay.effective_cell_wire import (
    EffectiveCellWire,
    effective_cell_to_wire,
)  # re-exported in __all__
from django_apps.asteroid_lab.typing_boundary import JsonObject

_LEGACY_SHAPE_OUTPUT_TOKENS = frozenset({"shape_belt", "belt", "shape"})
_LEGACY_FLUID_OUTPUT_TOKENS = frozenset({"fluid_pipe", "pipe", "fluid"})

_SPACE_TILE_PREFIXES = ("SpaceBelt_", "SpacePipe_")
_ROUTE_CELL_KINDS = frozenset({"space_belt", "space_pipe"})
_OCCUPANT_CELL_KINDS = frozenset(
    {
        "candidate_miner",
        "candidate_transport_stub",
        "candidate_route_path",
        "shape_miner",
        "fluid_miner",
        "shape_miner_extension",
        "fluid_miner_extension",
        "miner",
        "extension",
        "committed_miner",
        "building",
    }
)
_TERRAIN_CELL_KINDS = frozenset(
    {
        "asteroid_shape_field",
        "asteroid_fluid_field",
        "void",
        "empty",
    }
)


@dataclass(frozen=True, slots=True)
class EffectiveCellView:
    frame_index: int | None
    x: int
    y: int
    layer: int
    terrain_kind: str
    terrain_tile_type: str | None
    occupant_kind: str
    occupant_rotation: int | None
    transport_kind: str
    transport_tile_id: str | None
    simulation: str | None
    output_transport_kind: str
    sources: dict[str, object] = field(default_factory=dict)


def normalize_project_transport_kind(raw: object) -> str:
    value = str(raw or "").strip().lower()
    if not value or value == "none":
        return "none"
    if value in _LEGACY_SHAPE_OUTPUT_TOKENS or value == "space_belt":
        return "space_belt"
    if value in _LEGACY_FLUID_OUTPUT_TOKENS or value == "space_pipe":
        return "space_pipe"
    return "none"


def simulation_for_tile_id(tile_id: str | None) -> str | None:
    if not tile_id:
        return None
    if "Merger" in tile_id:
        return "SpaceMergerSimulation"
    if "Splitter" in tile_id:
        return "SpaceSplitterSimulation"
    if tile_id.startswith(_SPACE_TILE_PREFIXES):
        return "SpaceConveyorSimulation"
    return None


def _wire_cell_kind(cell: JsonObject) -> str:
    raw = cell.get("kind")
    if raw is None:
        raw = cell.get("cell_kind")
    return str(raw or "").strip()


def _wire_transport_raw(cell: JsonObject) -> str:
    raw = cell.get("transport")
    if raw is None:
        raw = cell.get("transport_kind")
    return str(raw or "").strip()


def _wire_output_transport_kind(cell: JsonObject) -> str:
    raw = cell.get("output_transport_kind")
    if raw is not None and str(raw).strip():
        normalized = normalize_project_transport_kind(raw)
        if normalized != "none":
            return normalized
    kind = _wire_cell_kind(cell)
    if _occupant_kind_from_cell(kind) is not None:
        return normalize_project_transport_kind(_wire_transport_raw(cell))
    return "none"


def _wire_tile_type(cell: JsonObject) -> str:
    raw = cell.get("tile_type")
    if raw is None:
        raw = cell.get("sprite_identifier")
    return str(raw or "").strip()


def _wire_rotation(cell: JsonObject) -> int | None:
    raw = cell.get("rotation")
    if raw is None:
        return None
    if not isinstance(raw, (int, str, float, bool)):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _wire_layer(cell: JsonObject, *, default: int = 0) -> int:
    raw = cell.get("layer")
    if raw is None:
        return default
    if not isinstance(raw, (int, str, float, bool)):
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _is_route_tile(tile_type: str, kind: str) -> bool:
    if tile_type.startswith(_SPACE_TILE_PREFIXES):
        return True
    return kind in _ROUTE_CELL_KINDS


def _occupant_kind_from_cell(kind: str) -> str | None:
    if not kind:
        return None
    if kind in _OCCUPANT_CELL_KINDS:
        if kind in {"shape_miner", "fluid_miner", "miner"}:
            return "committed_miner"
        if kind in {"shape_miner_extension", "fluid_miner_extension", "extension"}:
            return "extension"
        return kind
    return None


def merge_effective_cell_view(
    *,
    x: int,
    y: int,
    frame_index: int | None = None,
    full_cell: JsonObject | None = None,
    delta_cell: JsonObject | None = None,
    overlay_cells: list[JsonObject] | None = None,
) -> EffectiveCellView | None:
    """Merge map_view sources into one EffectiveCellView for ``(x, y)``."""

    base = delta_cell or full_cell
    if base is None and not overlay_cells:
        return None

    sources: dict[str, object] = {}
    if full_cell is not None:
        sources["full_cell"] = full_cell
    if delta_cell is not None:
        sources["delta_cell"] = delta_cell
    if overlay_cells:
        sources["overlay_cells"] = overlay_cells if len(overlay_cells) > 1 else overlay_cells[0]

    terrain_kind = "empty"
    terrain_tile_type: str | None = None
    occupant_kind = "none"
    occupant_rotation: int | None = None
    transport_kind = "none"
    transport_tile_id: str | None = None
    simulation: str | None = None
    output_transport_kind = "none"
    layer = 0

    for cell in (full_cell, delta_cell):
        if cell is None:
            continue
        kind = _wire_cell_kind(cell)
        tile_type = _wire_tile_type(cell)
        layer = _wire_layer(cell, default=layer)
        if kind in _TERRAIN_CELL_KINDS or (not kind and not tile_type):
            if kind:
                terrain_kind = kind
            if tile_type:
                terrain_tile_type = tile_type or None
        occupant = _occupant_kind_from_cell(kind)
        if occupant is not None:
            occupant_kind = occupant
            occupant_rotation = _wire_rotation(cell)
            profile = _wire_output_transport_kind(cell)
            if profile != "none":
                output_transport_kind = profile
        if _is_route_tile(tile_type, kind):
            transport_kind = normalize_project_transport_kind(kind or _wire_transport_raw(cell))
            if transport_kind == "none" and tile_type.startswith("SpacePipe_"):
                transport_kind = "space_pipe"
            elif transport_kind == "none" and tile_type.startswith("SpaceBelt_"):
                transport_kind = "space_belt"
            transport_tile_id = tile_type or None
            simulation = simulation_for_tile_id(transport_tile_id)

    if overlay_cells:
        for overlay in overlay_cells:
            kind = _wire_cell_kind(overlay)
            occupant = _occupant_kind_from_cell(kind)
            if occupant is not None:
                occupant_kind = occupant
                rot = _wire_rotation(overlay)
                if rot is not None:
                    occupant_rotation = rot
                profile = _wire_output_transport_kind(overlay)
                if profile != "none":
                    output_transport_kind = profile
                layer = _wire_layer(overlay, default=layer)
            tile_type = _wire_tile_type(overlay)
            if _is_route_tile(tile_type, kind):
                transport_kind = normalize_project_transport_kind(
                    kind or _wire_transport_raw(overlay)
                )
                if transport_kind == "none" and tile_type.startswith("SpacePipe_"):
                    transport_kind = "space_pipe"
                elif transport_kind == "none" and tile_type.startswith("SpaceBelt_"):
                    transport_kind = "space_belt"
                transport_tile_id = tile_type or None
                simulation = simulation_for_tile_id(transport_tile_id)
                layer = _wire_layer(overlay, default=layer)

    if base is None and overlay_cells:
        layer = _wire_layer(overlay_cells[0], default=layer)

    return EffectiveCellView(
        frame_index=frame_index,
        x=x,
        y=y,
        layer=layer,
        terrain_kind=terrain_kind,
        terrain_tile_type=terrain_tile_type,
        occupant_kind=occupant_kind,
        occupant_rotation=occupant_rotation,
        transport_kind=transport_kind,
        transport_tile_id=transport_tile_id,
        simulation=simulation,
        output_transport_kind=output_transport_kind,
        sources=sources,
    )


def effective_cell_view_as_dict(view: EffectiveCellView) -> dict[str, object]:
    return asdict(view)


__all__ = [
    "EffectiveCellView",
    "EffectiveCellWire",
    "effective_cell_to_wire",
    "effective_cell_view_as_dict",
    "merge_effective_cell_view",
    "normalize_project_transport_kind",
    "simulation_for_tile_id",
]
