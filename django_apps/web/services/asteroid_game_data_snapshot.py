"""Assemble frozen ``AsteroidGameDataSnapshot`` from pinned ``game_data`` import (web boundary)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from django_apps.asteroid_lab.optimization.game_data_contract_validation import (
    validate_building_snapshot,
)
from django_apps.asteroid_lab.optimization.game_data_contracts import (
    AsteroidGameDataSnapshot,
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    BuildingSnapshot,
    TransportRegistryEntry,
    build_snapshot_meta,
)
from django_apps.asteroid_lab.optimization.game_data_snapshot_hash import (
    snapshot_content_hash,
)
from django_apps.game_data.selectors.import_batch import (
    GAME_DATA_READ_ALIAS,
    pin_latest_import_batch,
)
from django_apps.game_data.snapshots.builder import build_game_data_row_bundle
from django_apps.game_data.snapshots.rows import BuildingAssemblyRow, TransportRegistryRow


def _utc_now_z() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _assembly_row_to_building(row: BuildingAssemblyRow) -> BuildingSnapshot:
    footprint_cells = tuple(
        BuildingFootprintCell(x=cell.x, y=cell.y, order_index=cell.order_index)
        for cell in row.footprint_cells
    )
    connectors = tuple(
        BuildingConnectorSnapshot(
            order_index=conn.order_index,
            connector_role=conn.connector_role,
            tile_direction=conn.tile_direction,
            io_channel_type=conn.io_channel_type,
            position_x=conn.position_x,
            position_y=conn.position_y,
            position_z=conn.position_z,
        )
        for conn in row.connectors
    )
    building = BuildingSnapshot(
        canonical_id=row.canonical_id,
        internal_name=row.internal_name,
        footprint_cells=footprint_cells,
        connectors=connectors,
    )
    return validate_building_snapshot(building)


def _transport_row_to_entry(row: TransportRegistryRow) -> TransportRegistryEntry:
    return TransportRegistryEntry(
        transport_kind=row.transport_kind,
        transport_category=row.transport_category,
        building_variant_canonical_id=row.building_variant_canonical_id,
    )


def build_asteroid_game_data_snapshot(
    *,
    db_alias: str = GAME_DATA_READ_ALIAS,
) -> AsteroidGameDataSnapshot:
    """Pin latest import batch, materialize ordered rows, return immutable consumer snapshot."""
    batch = pin_latest_import_batch(db_alias=db_alias)
    bundle = build_game_data_row_bundle(batch.pk, db_alias=db_alias)
    buildings = tuple(
        _assembly_row_to_building(row)
        for row in sorted(bundle.buildings, key=lambda b: (b.internal_name, b.canonical_id))
    )
    transport_registry = tuple(_transport_row_to_entry(row) for row in bundle.transport_registry)
    meta = build_snapshot_meta(
        data_revision=batch.manifest_self_hash,
        db_alias=db_alias,
        built_at_utc=_utc_now_z(),
        content_hash="pending",
        game_version=batch.game_version,
    )
    snap = AsteroidGameDataSnapshot(
        meta=meta,
        buildings=buildings,
        transport_registry=transport_registry,
    )
    content_hash = snapshot_content_hash(snap)
    return replace(snap, meta=replace(snap.meta, content_hash=content_hash))
