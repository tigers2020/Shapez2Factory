"""Shim: relocated to ``shapez2_factory.domain.asteroid_lab.game_data_snapshot`` (PR-CLI-2a).

Re-exports the pure core snapshot DTOs so existing ``django_apps`` imports keep working.
Import the core module directly in new code.
"""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.game_data_snapshot import (
    RULE_VERSION,
    SCHEMA_VERSION,
    AsteroidGameDataSnapshot,
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    BuildingSnapshot,
    SnapshotMeta,
    TransportRegistryEntry,
    build_snapshot_meta,
    snapshot_content_hash,
    validate_building_snapshot,
)

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
