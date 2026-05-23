"""Frozen consumer DTOs and validation for game_data → Asteroid Lab snapshot."""

from __future__ import annotations

import hashlib
import json
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
        if not isinstance(self.connectors, tuple):
            raise TypeError("connectors must be tuple")


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


def _sort_footprint(
    cells: tuple[BuildingFootprintCell, ...],
) -> tuple[BuildingFootprintCell, ...]:
    return tuple(sorted(cells, key=lambda c: (c.y, c.x, c.order_index)))


def _sort_connectors(
    connectors: tuple[BuildingConnectorSnapshot, ...],
) -> tuple[BuildingConnectorSnapshot, ...]:
    return tuple(sorted(connectors, key=lambda c: c.order_index))


def validate_building_snapshot(building: BuildingSnapshot) -> BuildingSnapshot:
    if not isinstance(building.footprint_cells, tuple):
        raise TypeError("footprint_cells must be tuple")
    if not isinstance(building.connectors, tuple):
        raise TypeError("connectors must be tuple")
    ordered_fp = _sort_footprint(building.footprint_cells)
    ordered_conn = _sort_connectors(building.connectors)
    if building.footprint_cells is not ordered_fp or building.connectors is not ordered_conn:
        return BuildingSnapshot(
            canonical_id=building.canonical_id,
            internal_name=building.internal_name,
            footprint_cells=ordered_fp,
            connectors=ordered_conn,
        )
    return building


def _footprint_cell_dict(cell: BuildingFootprintCell) -> dict[str, int]:
    return {
        "order_index": cell.order_index,
        "x": cell.x,
        "y": cell.y,
    }


def _connector_dict(connector: BuildingConnectorSnapshot) -> dict[str, int | str]:
    return {
        "connector_role": connector.connector_role,
        "io_channel_type": connector.io_channel_type,
        "order_index": connector.order_index,
        "position_x": connector.position_x,
        "position_y": connector.position_y,
        "position_z": connector.position_z,
        "tile_direction": connector.tile_direction,
    }


def _building_dict(building: BuildingSnapshot) -> dict[str, object]:
    footprint_cells = sorted(
        building.footprint_cells,
        key=lambda c: (c.y, c.x, c.order_index),
    )
    connectors = sorted(building.connectors, key=lambda c: c.order_index)
    return {
        "canonical_id": building.canonical_id,
        "connectors": [_connector_dict(c) for c in connectors],
        "footprint_cells": [_footprint_cell_dict(c) for c in footprint_cells],
        "internal_name": building.internal_name,
    }


def _transport_dict(entry: TransportRegistryEntry) -> dict[str, str]:
    return {
        "building_variant_canonical_id": entry.building_variant_canonical_id,
        "transport_category": entry.transport_category,
        "transport_kind": entry.transport_kind,
    }


def _canonical_payload(snapshot: AsteroidGameDataSnapshot) -> dict[str, object]:
    buildings = sorted(
        snapshot.buildings,
        key=lambda b: (b.internal_name, b.canonical_id),
    )
    transport_registry = sorted(
        snapshot.transport_registry,
        key=lambda e: e.transport_kind,
    )
    return {
        "buildings": [_building_dict(b) for b in buildings],
        "transport_registry": [_transport_dict(e) for e in transport_registry],
    }


def snapshot_content_hash(snapshot: AsteroidGameDataSnapshot) -> str:
    """SHA-256 hex of canonical JSON over snapshot subset (meta excluded)."""

    blob = json.dumps(
        _canonical_payload(snapshot),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


__all__ = [
    "SCHEMA_VERSION",
    "RULE_VERSION",
    "AsteroidGameDataSnapshot",
    "BuildingConnectorSnapshot",
    "BuildingFootprintCell",
    "BuildingSnapshot",
    "SnapshotMeta",
    "TransportRegistryEntry",
    "build_snapshot_meta",
    "snapshot_content_hash",
    "validate_building_snapshot",
]
