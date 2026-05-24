"""Assemble ``AsteroidGameDataSnapshot`` from pinned ``game_data`` import batch."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime

from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
    catalog_slice_from_snapshot,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    AsteroidGameDataSnapshot,
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    BuildingSnapshot,
    TransportRegistryEntry,
    build_snapshot_meta,
    snapshot_content_hash,
    validate_building_snapshot,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    GameDataSnapshotProvenance,
    provenance_from_snapshot,
)
from django_apps.game_data.models import ImportBatch
from django_apps.game_data.selectors.import_batch import pin_latest_import_batch
from django_apps.game_data.snapshots.builder import build_game_data_row_bundle
from django_apps.game_data.snapshots.rows import (
    BuildingAssemblyRow,
    ConnectorRow,
    FootprintCellRow,
    TransportRegistryRow,
)


@dataclass(frozen=True, slots=True)
class GameDataSnapshotBuildResult:
    snapshot: AsteroidGameDataSnapshot
    provenance: GameDataSnapshotProvenance
    catalog_slice: BuildingCatalogSlice


def _footprint_dto(row: FootprintCellRow) -> BuildingFootprintCell:
    return BuildingFootprintCell(x=row.x, y=row.y, order_index=row.order_index)


def _connector_dto(row: ConnectorRow) -> BuildingConnectorSnapshot:
    return BuildingConnectorSnapshot(
        order_index=row.order_index,
        connector_role=row.connector_role,
        tile_direction=row.tile_direction,
        io_channel_type=row.io_channel_type,
        position_x=row.position_x,
        position_y=row.position_y,
        position_z=row.position_z,
    )


def _building_dto(row: BuildingAssemblyRow) -> BuildingSnapshot:
    building = BuildingSnapshot(
        canonical_id=row.canonical_id,
        internal_name=row.internal_name,
        footprint_cells=tuple(_footprint_dto(c) for c in row.footprint_cells),
        connectors=tuple(_connector_dto(c) for c in row.connectors),
    )
    return validate_building_snapshot(building)


def _transport_dto(row: TransportRegistryRow) -> TransportRegistryEntry:
    return TransportRegistryEntry(
        transport_kind=row.transport_kind,
        transport_category=row.transport_category,
        building_variant_canonical_id=row.building_variant_canonical_id,
    )


def _build_asteroid_game_data_snapshot_for_batch(
    batch: ImportBatch,
    *,
    db_alias: str,
) -> AsteroidGameDataSnapshot:
    bundle = build_game_data_row_bundle(batch.pk, db_alias=db_alias)
    buildings = tuple(
        _building_dto(b)
        for b in sorted(bundle.buildings, key=lambda b: (b.internal_name, b.canonical_id))
    )
    transport_registry = tuple(
        _transport_dto(r) for r in sorted(bundle.transport_registry, key=lambda t: t.transport_kind)
    )
    built_at_utc = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta = build_snapshot_meta(
        data_revision=batch.manifest_self_hash,
        db_alias=db_alias,
        built_at_utc=built_at_utc,
        content_hash="",
        game_version=batch.game_version,
    )
    snap = AsteroidGameDataSnapshot(
        meta=meta,
        buildings=buildings,
        transport_registry=transport_registry,
    )
    content_hash = snapshot_content_hash(snap)
    return replace(snap, meta=replace(snap.meta, content_hash=content_hash))


def build_asteroid_game_data_snapshot_with_provenance(
    *,
    db_alias: str = "default",
) -> GameDataSnapshotBuildResult:
    """Pin latest import batch once; return snapshot + provenance (sole construction site)."""

    batch = pin_latest_import_batch(db_alias=db_alias)
    snapshot = _build_asteroid_game_data_snapshot_for_batch(batch, db_alias=db_alias)
    catalog_slice = catalog_slice_from_snapshot(snapshot)
    provenance = provenance_from_snapshot(
        snapshot,
        import_batch_id=int(batch.pk),
        catalog_slice=catalog_slice,
    )
    return GameDataSnapshotBuildResult(
        snapshot=snapshot,
        provenance=provenance,
        catalog_slice=catalog_slice,
    )


def build_asteroid_game_data_snapshot(*, db_alias: str = "default") -> AsteroidGameDataSnapshot:
    """Return snapshot only; prefer ``build_asteroid_game_data_snapshot_with_provenance``."""

    return build_asteroid_game_data_snapshot_with_provenance(db_alias=db_alias).snapshot


__all__ = [
    "GameDataSnapshotBuildResult",
    "build_asteroid_game_data_snapshot",
    "build_asteroid_game_data_snapshot_with_provenance",
]
