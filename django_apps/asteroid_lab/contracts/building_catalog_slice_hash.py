"""Deterministic hash for ``BuildingCatalogSlice`` (Track B2)."""

from __future__ import annotations

import hashlib
import json

from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
    VariantIdentity,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import TransportRegistryEntry


def _variant_dict(v: VariantIdentity) -> dict[str, str]:
    return {"canonical_id": v.canonical_id, "internal_name": v.internal_name}


def _transport_dict(e: TransportRegistryEntry) -> dict[str, str]:
    return {
        "building_variant_canonical_id": e.building_variant_canonical_id,
        "transport_category": e.transport_category,
        "transport_kind": e.transport_kind,
    }


def _canonical_payload(sl: BuildingCatalogSlice) -> dict[str, object]:
    registry = sorted(sl.transport_registry, key=lambda e: e.transport_kind)
    variants = sorted(sl.variants, key=lambda v: (v.internal_name, v.canonical_id))
    return {
        "slice_version": sl.slice_version,
        "transport_registry": [_transport_dict(e) for e in registry],
        "variants": [_variant_dict(v) for v in variants],
    }


def catalog_slice_hash(sl: BuildingCatalogSlice) -> str:
    """SHA-256 hex; ``slice_version`` is included in the payload."""

    blob = json.dumps(_canonical_payload(sl), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


__all__ = ["catalog_slice_hash"]
