from __future__ import annotations

from django_apps.game_data.models import TransportBuildingRegistry
from django_apps.game_data.selectors.buildings import GAME_DATA_READ_ALIAS


def fetch_transport_rows_for_batch(
    batch_id: int,
    *,
    db_alias: str = GAME_DATA_READ_ALIAS,
) -> list:
    return list(
        TransportBuildingRegistry.objects.using(db_alias)
        .filter(import_batch_id=batch_id)
        .order_by("transport_kind")
        .values_list(
            "transport_kind",
            "transport_category",
            "building_variant__canonical_id",
            named=True,
        )
    )
