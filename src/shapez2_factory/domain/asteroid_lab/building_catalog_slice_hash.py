"""Deterministic hash for ``BuildingCatalogSlice`` (Track B2 / D)."""

from __future__ import annotations

import hashlib
import json

from shapez2_factory.domain.asteroid_lab.building_catalog_slice import (
    BuildingCatalogSlice,
    VariantGeometryCatalog,
    VariantIdentity,
)
from shapez2_factory.domain.asteroid_lab.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    TransportRegistryEntry,
)


def _variant_dict(v: VariantIdentity) -> dict[str, str]:
    return {"canonical_id": v.canonical_id, "internal_name": v.internal_name}


def _footprint_dict(cell: BuildingFootprintCell) -> dict[str, int]:
    return {"order_index": cell.order_index, "x": cell.x, "y": cell.y}


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


def _geometry_dict(g: VariantGeometryCatalog) -> dict[str, object]:
    return {
        "canonical_id": g.canonical_id,
        "connectors": [_connector_dict(c) for c in g.connectors],
        "footprint_cells": [_footprint_dict(c) for c in g.footprint_cells],
        "internal_name": g.internal_name,
    }


def _transport_dict(e: TransportRegistryEntry) -> dict[str, str]:
    return {
        "building_variant_canonical_id": e.building_variant_canonical_id,
        "transport_category": e.transport_category,
        "transport_kind": e.transport_kind,
    }


def _canonical_payload(sl: BuildingCatalogSlice) -> dict[str, object]:
    registry = sorted(sl.transport_registry, key=lambda e: e.transport_kind)
    variants = sorted(sl.variants, key=lambda v: (v.internal_name, v.canonical_id))
    geometries = sorted(
        sl.variant_geometries,
        key=lambda g: (g.internal_name, g.canonical_id),
    )
    return {
        "slice_version": sl.slice_version,
        "transport_registry": [_transport_dict(e) for e in registry],
        "variant_geometries": [_geometry_dict(g) for g in geometries],
        "variants": [_variant_dict(v) for v in variants],
    }


def catalog_slice_hash(sl: BuildingCatalogSlice) -> str:
    """SHA-256 hex; ``slice_version`` is included in the payload."""

    blob = json.dumps(_canonical_payload(sl), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


__all__ = ["catalog_slice_hash"]
