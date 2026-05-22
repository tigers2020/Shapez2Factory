"""Canonical ordering for game_data consumer snapshot DTOs."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.game_data_contracts import (
    BuildingFootprintCell,
    BuildingSnapshot,
)


def _sort_footprint(
    cells: tuple[BuildingFootprintCell, ...],
) -> tuple[BuildingFootprintCell, ...]:
    return tuple(sorted(cells, key=lambda c: (c.y, c.x, c.order_index)))


def validate_building_snapshot(building: BuildingSnapshot) -> BuildingSnapshot:
    if not isinstance(building.footprint_cells, tuple):
        raise TypeError("footprint_cells must be tuple")
    ordered_fp = _sort_footprint(building.footprint_cells)
    if building.footprint_cells is not ordered_fp:
        return BuildingSnapshot(
            canonical_id=building.canonical_id,
            internal_name=building.internal_name,
            footprint_cells=ordered_fp,
            connectors=building.connectors,
        )
    return building
