from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FootprintCellRow:
    x: int
    y: int
    order_index: int


@dataclass(frozen=True, slots=True)
class ConnectorRow:
    order_index: int
    connector_role: str
    tile_direction: str
    io_channel_type: str
    position_x: int
    position_y: int
    position_z: int


@dataclass(frozen=True, slots=True)
class BuildingAssemblyRow:
    canonical_id: str
    internal_name: str
    footprint_cells: tuple[FootprintCellRow, ...]
    connectors: tuple[ConnectorRow, ...]


@dataclass(frozen=True, slots=True)
class TransportRegistryRow:
    transport_kind: str
    transport_category: str
    building_variant_canonical_id: str


@dataclass(frozen=True, slots=True)
class GameDataRowBundle:
    buildings: tuple[BuildingAssemblyRow, ...]
    transport_registry: tuple[TransportRegistryRow, ...]
