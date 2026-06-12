"""EffectiveCellView — merged terrain / occupant / transport / output for Lab cell detail UI."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from django_apps.asteroid_lab.replay.effective_cell_wire import (
    EffectiveCellWire,
    effective_cell_to_wire,
)  # re-exported in __all__
from django_apps.asteroid_lab.replay.replay_cell_semantics import (
    TERRAIN_CELL_KINDS,
    is_route_tile,
    normalize_project_transport_kind,
    occupant_kind_from_cell,
    overlay_role_from_cell,
    resolve_route_transport_kind,
    simulation_for_tile_id,
)
from django_apps.asteroid_lab.replay.replay_map_cell_wire import (
    wire_field_kind,
    wire_field_tile_type,
    wire_field_transport,
)
from django_apps.asteroid_lab.typing_boundary import JsonObject


@dataclass(frozen=True, slots=True)
class EffectiveCellView:
    frame_index: int | None
    x: int
    y: int
    layer: int
    terrain_kind: str
    terrain_tile_type: str | None
    occupant_kind: str
    occupant_wire_kind: str | None
    occupant_sprite_id: str | None
    occupant_rotation: int | None
    transport_kind: str
    transport_tile_id: str | None
    simulation: str | None
    output_transport_kind: str
    overlay_role: str | None = None
    sources: dict[str, object] = field(default_factory=dict)


def _wire_output_transport_kind(cell: JsonObject) -> str:
    raw = cell.get("output_transport_kind")
    if raw is not None and str(raw).strip():
        normalized = normalize_project_transport_kind(raw)
        if normalized != "none":
            return normalized
    kind = wire_field_kind(cell).strip()
    if occupant_kind_from_cell(kind) is not None:
        return normalize_project_transport_kind(wire_field_transport(cell))
    return "none"


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
    occupant_wire_kind: str | None = None
    occupant_sprite_id: str | None = None
    occupant_rotation: int | None = None
    transport_kind = "none"
    transport_tile_id: str | None = None
    simulation: str | None = None
    output_transport_kind = "none"
    overlay_role: str | None = None
    layer = 0

    for cell in (full_cell, delta_cell):
        if cell is None:
            continue
        kind = wire_field_kind(cell).strip()
        tile_type = wire_field_tile_type(cell).strip()
        layer = _wire_layer(cell, default=layer)
        if kind in TERRAIN_CELL_KINDS or (not kind and not tile_type):
            if kind:
                terrain_kind = kind
            if tile_type:
                terrain_tile_type = tile_type or None
        occupant = occupant_kind_from_cell(kind)
        if occupant is not None:
            occupant_kind = occupant
            if kind:
                occupant_wire_kind = kind
            occupant_rotation = _wire_rotation(cell)
            profile = _wire_output_transport_kind(cell)
            if profile != "none":
                output_transport_kind = profile
            if tile_type and not is_route_tile(tile_type, kind):
                occupant_sprite_id = tile_type or None
        if is_route_tile(tile_type, kind):
            transport_kind = resolve_route_transport_kind(
                tile_type, kind, wire_field_transport(cell)
            )
            transport_tile_id = tile_type or None
            simulation = simulation_for_tile_id(transport_tile_id)

    if overlay_cells:
        for overlay in overlay_cells:
            kind = wire_field_kind(overlay).strip()
            role = overlay_role_from_cell(overlay)
            if role:
                overlay_role = role
            profile = _wire_output_transport_kind(overlay)
            if profile != "none" and occupant_kind_from_cell(kind) is None:
                output_transport_kind = profile
            occupant = occupant_kind_from_cell(kind)
            if occupant is not None:
                occupant_kind = occupant
                if kind:
                    occupant_wire_kind = kind
                rot = _wire_rotation(overlay)
                if rot is not None:
                    occupant_rotation = rot
                occ_profile = _wire_output_transport_kind(overlay)
                if occ_profile != "none":
                    output_transport_kind = occ_profile
                occ_tile = wire_field_tile_type(overlay).strip()
                if occ_tile and not is_route_tile(occ_tile, kind):
                    occupant_sprite_id = occ_tile or None
                layer = _wire_layer(overlay, default=layer)
            tile_type = wire_field_tile_type(overlay).strip()
            if is_route_tile(tile_type, kind):
                transport_kind = resolve_route_transport_kind(
                    tile_type, kind, wire_field_transport(overlay)
                )
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
        occupant_wire_kind=occupant_wire_kind,
        occupant_sprite_id=occupant_sprite_id,
        occupant_rotation=occupant_rotation,
        transport_kind=transport_kind,
        transport_tile_id=transport_tile_id,
        simulation=simulation,
        output_transport_kind=output_transport_kind,
        overlay_role=overlay_role,
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
