from __future__ import annotations

from collections import defaultdict

from django_apps.game_data.selectors.buildings import (
    GAME_DATA_READ_ALIAS,
    fetch_building_rows_for_batch,
)
from django_apps.game_data.selectors.transport_registry import (
    fetch_transport_rows_for_batch,
)
from django_apps.game_data.snapshots.errors import SnapshotBuildError, SnapshotBuildErrorCode
from django_apps.game_data.snapshots.rows import (
    BuildingAssemblyRow,
    ConnectorRow,
    FootprintCellRow,
    GameDataRowBundle,
    TransportRegistryRow,
)


def _footprint_sort_key(row) -> tuple[int, int, int]:
    return (row.y, row.x, row.order_index)


def _connector_sort_key(row) -> int:
    return row.order_index


def build_game_data_row_bundle(
    batch_id: int,
    *,
    db_alias: str = GAME_DATA_READ_ALIAS,
) -> GameDataRowBundle:
    building_rows = fetch_building_rows_for_batch(batch_id, db_alias=db_alias)
    variant_ids = {variant.id for variant in building_rows.variants}

    footprints_by_variant: dict[int, list] = defaultdict(list)
    for footprint in building_rows.footprints:
        variant_id = footprint.building_variant_id
        if variant_id not in variant_ids:
            raise SnapshotBuildError(
                SnapshotBuildErrorCode.ORPHAN_FOOTPRINT,
                f"footprint references unknown building_variant_id={variant_id}",
            )
        footprints_by_variant[variant_id].append(footprint)

    connectors_by_variant: dict[int, list] = defaultdict(list)
    for connector in building_rows.connectors:
        variant_id = connector.building_variant_id
        if variant_id not in variant_ids:
            raise SnapshotBuildError(
                SnapshotBuildErrorCode.ORPHAN_FOOTPRINT,
                f"connector references unknown building_variant_id={variant_id}",
            )
        connectors_by_variant[variant_id].append(connector)

    buildings: list[BuildingAssemblyRow] = []
    for variant in building_rows.variants:
        footprint_cells = tuple(
            FootprintCellRow(x=fp.x, y=fp.y, order_index=fp.order_index)
            for fp in sorted(
                footprints_by_variant[variant.id],
                key=_footprint_sort_key,
            )
        )
        connectors = tuple(
            ConnectorRow(
                order_index=conn.order_index,
                connector_role=conn.connector_role,
                tile_direction=conn.tile_direction,
                io_channel_type=conn.io_channel_type,
                position_x=conn.position_x,
                position_y=conn.position_y,
                position_z=conn.position_z,
            )
            for conn in sorted(
                connectors_by_variant[variant.id],
                key=_connector_sort_key,
            )
        )
        buildings.append(
            BuildingAssemblyRow(
                canonical_id=variant.canonical_id,
                internal_name=variant.internal_name,
                footprint_cells=footprint_cells,
                connectors=connectors,
            )
        )

    transport_registry = tuple(
        TransportRegistryRow(
            transport_kind=row.transport_kind,
            transport_category=row.transport_category,
            building_variant_canonical_id=row.building_variant__canonical_id,
        )
        for row in fetch_transport_rows_for_batch(batch_id, db_alias=db_alias)
    )

    return GameDataRowBundle(
        buildings=tuple(buildings),
        transport_registry=transport_registry,
    )
