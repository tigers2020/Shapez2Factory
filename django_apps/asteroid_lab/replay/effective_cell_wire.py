"""Effective cell UI read-model wire shapes (JSON projection authority only)."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from django_apps.asteroid_lab.replay.effective_cell_view import EffectiveCellView


class EffectiveCellCoordWire(TypedDict):
    x: int
    y: int
    layer: int


class EffectiveCellTerrainWire(TypedDict):
    kind: str
    tile_type: str | None


class EffectiveCellOccupantWire(TypedDict):
    kind: str
    rotation: int | None


class EffectiveCellTransportWire(TypedDict):
    kind: str
    tile_id: str | None
    simulation: str | None


class EffectiveCellOutputWire(TypedDict):
    transport_kind: str


class EffectiveCellWire(TypedDict):
    frame_index: int | None
    coord: EffectiveCellCoordWire
    terrain: EffectiveCellTerrainWire
    occupant: EffectiveCellOccupantWire
    transport: EffectiveCellTransportWire
    output: EffectiveCellOutputWire
    sources: dict[str, object]


def effective_cell_to_wire(view: EffectiveCellView) -> EffectiveCellWire:
    """Serialize one EffectiveCellView to its named wire contract."""

    return {
        "frame_index": view.frame_index,
        "coord": {"x": view.x, "y": view.y, "layer": view.layer},
        "terrain": {
            "kind": view.terrain_kind,
            "tile_type": view.terrain_tile_type,
        },
        "occupant": {
            "kind": view.occupant_kind,
            "rotation": view.occupant_rotation,
        },
        "transport": {
            "kind": view.transport_kind,
            "tile_id": view.transport_tile_id,
            "simulation": view.simulation,
        },
        "output": {"transport_kind": view.output_transport_kind},
        "sources": dict(view.sources),
    }


__all__ = [
    "EffectiveCellCoordWire",
    "EffectiveCellOccupantWire",
    "EffectiveCellOutputWire",
    "EffectiveCellTerrainWire",
    "EffectiveCellTransportWire",
    "EffectiveCellWire",
    "effective_cell_to_wire",
]
