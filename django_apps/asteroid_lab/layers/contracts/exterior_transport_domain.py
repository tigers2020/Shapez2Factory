"""Bounded virtual exterior install/search domain for L3 route probe (candidate stage only)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.snapshots.grid_contract import BBox, Coord


@dataclass(frozen=True, slots=True)
class ExteriorTransportDomain:
    """Exterior install/search space for one L3 probe — not a transport network (spec §3.6)."""

    search_bbox: BBox
    blocked_field_cells: frozenset[Coord]
    placeable_cells: frozenset[Coord]


__all__ = ["ExteriorTransportDomain"]
