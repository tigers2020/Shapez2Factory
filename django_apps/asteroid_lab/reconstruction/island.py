"""Shim — relocated to ``shapez2_factory.domain.asteroid_lab.reconstruction.island`` (PR-CLI-2f)."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.reconstruction.island import (
    CellKey,
    build_original_evidence_by_xy,
    resolve_island_kind,
    stamp_islands_uniform,
)

__all__ = [
    "CellKey",
    "build_original_evidence_by_xy",
    "resolve_island_kind",
    "stamp_islands_uniform",
]
