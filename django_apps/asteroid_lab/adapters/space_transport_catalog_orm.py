"""Sanctioned ORM → ``SpaceTransportTileCatalog`` bridge (game_data registry only)."""

from __future__ import annotations

from typing import Any

from django_apps.game_data.services.space_transport_layout_catalog import (
    build_space_transport_catalog_payload_from_orm,
    build_space_transport_catalog_payload_from_snapshot_layouts,
)
from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
    SpaceTransportTileCatalog,
)


def try_load_space_transport_catalog_from_orm() -> SpaceTransportTileCatalog | None:
    payload = build_space_transport_catalog_payload_from_orm()
    if payload is None:
        return None
    return SpaceTransportTileCatalog.from_payload(payload)


def try_load_space_transport_catalog_from_snapshot_layouts(
    layouts: list[dict[str, Any]],
) -> SpaceTransportTileCatalog | None:
    try:
        catalog_payload = build_space_transport_catalog_payload_from_snapshot_layouts(layouts)
    except ValueError:
        return None
    return SpaceTransportTileCatalog.from_payload(catalog_payload)


__all__ = [
    "try_load_space_transport_catalog_from_orm",
    "try_load_space_transport_catalog_from_snapshot_layouts",
]
