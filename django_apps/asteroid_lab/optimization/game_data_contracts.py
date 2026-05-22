"""Frozen consumer DTOs for game_data → Asteroid Lab snapshot (no Django imports)."""

from __future__ import annotations

from dataclasses import dataclass

SCHEMA_VERSION = "game_data_snapshot_v1"
RULE_VERSION = "asteroid_v0"


@dataclass(frozen=True, slots=True)
class SnapshotMeta:
    schema_version: str
    data_revision: str
    db_alias: str
    built_at_utc: str
    content_hash: str
    game_version: str
    rule_version: str


def build_snapshot_meta(
    *,
    data_revision: str,
    db_alias: str,
    built_at_utc: str,
    content_hash: str,
    game_version: str,
) -> SnapshotMeta:
    return SnapshotMeta(
        schema_version=SCHEMA_VERSION,
        data_revision=data_revision,
        db_alias=db_alias,
        built_at_utc=built_at_utc,
        content_hash=content_hash,
        game_version=game_version,
        rule_version=RULE_VERSION,
    )


@dataclass(frozen=True, slots=True)
class BuildingFootprintCell:
    x: int
    y: int
    order_index: int


@dataclass(frozen=True, slots=True)
class BuildingConnectorSnapshot:
    order_index: int
    connector_role: str
    tile_direction: str
    io_channel_type: str
    position_x: int
    position_y: int
    position_z: int


@dataclass(frozen=True, slots=True)
class BuildingSnapshot:
    canonical_id: str
    internal_name: str
    footprint_cells: tuple[BuildingFootprintCell, ...]
    connectors: tuple[BuildingConnectorSnapshot, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.footprint_cells, tuple):
            raise TypeError("footprint_cells must be tuple")


@dataclass(frozen=True, slots=True)
class TransportRegistryEntry:
    transport_kind: str
    transport_category: str
    building_variant_canonical_id: str


@dataclass(frozen=True, slots=True)
class AsteroidGameDataSnapshot:
    meta: SnapshotMeta
    buildings: tuple[BuildingSnapshot, ...]
    transport_registry: tuple[TransportRegistryEntry, ...]
