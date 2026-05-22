"""Deterministic content_hash for AsteroidGameDataSnapshot (solver subset only)."""

from __future__ import annotations

import hashlib
import json

from django_apps.asteroid_lab.optimization.game_data_contracts import (
    AsteroidGameDataSnapshot,
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    BuildingSnapshot,
    TransportRegistryEntry,
)


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
    """SHA-256 hex of canonical JSON over solver subset (meta excluded)."""
    blob = json.dumps(
        _canonical_payload(snapshot),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
