"""Shim — relocated to ``shapez2_factory.domain.asteroid_lab.reconstruction.evidence`` (2c)."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.reconstruction.evidence import (
    ASTEROID_FIELD_KINDS,
    MINER_EXTENSION_CELL_KINDS,
    evidence_field_kind,
    inferred_field_kind_from_removed_miner_extension,
    is_asteroid_evidence,
    is_strippable_building,
)

__all__ = [
    "ASTEROID_FIELD_KINDS",
    "MINER_EXTENSION_CELL_KINDS",
    "evidence_field_kind",
    "inferred_field_kind_from_removed_miner_extension",
    "is_asteroid_evidence",
    "is_strippable_building",
]
