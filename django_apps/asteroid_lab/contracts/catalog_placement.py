"""Catalog placement audit contracts (Track D+)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from django_apps.asteroid_lab.optimization.coords import Coord


class CardinalDirection(StrEnum):
    """Cardinal rotation on island grid (matches RTTP pattern library wire)."""

    N = "N"
    E = "E"
    S = "S"
    W = "W"


class CatalogPlacementIssueCode(StrEnum):
    CATALOG_VARIANT_MAPPING_MISSING = "catalog_variant_mapping_missing"
    CATALOG_VARIANT_NOT_IN_SLICE = "catalog_variant_not_in_slice"
    CATALOG_FOOTPRINT_MISMATCH = "catalog_footprint_mismatch"
    CATALOG_CONNECTOR_MISMATCH = "catalog_connector_mismatch"
    CATALOG_ANCHOR_TRANSFORM_ERROR = "catalog_anchor_transform_error"
    CATALOG_ROTATION_UNSUPPORTED = "catalog_rotation_unsupported"


@dataclass(frozen=True, slots=True)
class CatalogPlacementRef:
    canonical_id: str
    anchor_coord: Coord
    rotation: CardinalDirection


@dataclass(frozen=True, slots=True)
class CatalogPlacementAudit:
    catalog_validation_mode: Literal["observe_only"]
    checked_candidate_count: int
    matched_candidate_count: int
    mismatch_candidate_count: int
    unmapped_candidate_count: int
    not_in_slice_count: int
    transform_error_count: int
    issue_codes: tuple[str, ...]


__all__ = [
    "CardinalDirection",
    "CatalogPlacementAudit",
    "CatalogPlacementIssueCode",
    "CatalogPlacementRef",
]
