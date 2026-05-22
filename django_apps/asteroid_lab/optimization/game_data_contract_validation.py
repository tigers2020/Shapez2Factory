"""Canonical ordering for game_data consumer snapshot DTOs."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.game_data_contracts import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    BuildingSnapshot,
)


def _sort_footprint(
    cells: tuple[BuildingFootprintCell, ...],
) -> tuple[BuildingFootprintCell, ...]:
    return tuple(sorted(cells, key=lambda c: (c.y, c.x, c.order_index)))


def _sort_connectors(
    connectors: tuple[BuildingConnectorSnapshot, ...],
) -> tuple[BuildingConnectorSnapshot, ...]:
    return tuple(sorted(connectors, key=lambda c: c.order_index))


def validate_building_snapshot(building: BuildingSnapshot) -> BuildingSnapshot:
    if not isinstance(building.footprint_cells, tuple):
        raise TypeError("footprint_cells must be tuple")
    if not isinstance(building.connectors, tuple):
        raise TypeError("connectors must be tuple")
    ordered_fp = _sort_footprint(building.footprint_cells)
    ordered_conn = _sort_connectors(building.connectors)
    if building.footprint_cells is not ordered_fp or building.connectors is not ordered_conn:
        return BuildingSnapshot(
            canonical_id=building.canonical_id,
            internal_name=building.internal_name,
            footprint_cells=ordered_fp,
            connectors=ordered_conn,
        )
    return building
