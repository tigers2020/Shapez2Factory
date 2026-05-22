from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from django_apps.game_data.models import (
    BuildingConnector,
    BuildingFootprintTile,
    BuildingVariant,
)

GAME_DATA_READ_ALIAS = "default"


class BuildingVariantRow(NamedTuple):
    id: int
    canonical_id: str
    internal_name: str


class BuildingFootprintRow(NamedTuple):
    building_variant_id: int
    x: int
    y: int
    order_index: int


class BuildingConnectorRow(NamedTuple):
    building_variant_id: int
    order_index: int
    connector_role: str
    tile_direction: str
    io_channel_type: str
    position_x: int
    position_y: int
    position_z: int


@dataclass(frozen=True)
class BuildingRowsBundle:
    variants: list[BuildingVariantRow]
    footprints: list[BuildingFootprintRow]
    connectors: list[BuildingConnectorRow]


def fetch_building_rows_for_batch(
    batch_id: int,
    *,
    db_alias: str = GAME_DATA_READ_ALIAS,
) -> BuildingRowsBundle:
    variants: list[BuildingVariantRow] = list(
        BuildingVariant.objects.using(db_alias)
        .filter(import_batch_id=batch_id)
        .order_by("internal_name", "canonical_id")
        .values_list("id", "canonical_id", "internal_name", named=True)
    )
    footprints: list[BuildingFootprintRow] = list(
        BuildingFootprintTile.objects.using(db_alias)
        .filter(building_variant__import_batch_id=batch_id)
        .order_by("building_variant_id", "order_index")
        .values_list("building_variant_id", "x", "y", "order_index", named=True)
    )
    connectors: list[BuildingConnectorRow] = list(
        BuildingConnector.objects.using(db_alias)
        .filter(building_variant__import_batch_id=batch_id)
        .order_by("building_variant_id", "order_index")
        .values_list(
            "building_variant_id",
            "order_index",
            "connector_role",
            "tile_direction",
            "io_channel_type",
            "position_x",
            "position_y",
            "position_z",
            named=True,
        )
    )
    return BuildingRowsBundle(
        variants=variants,
        footprints=footprints,
        connectors=connectors,
    )
