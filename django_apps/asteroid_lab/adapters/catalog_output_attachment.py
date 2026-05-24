"""Catalog output stub/dir from variant connectors (Track D+ PR-3)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    CatalogTransformError,
    cardinal_unit_vector,
    expected_footprint_coords,
    rotate_cardinal_direction,
    rotate_coord,
    tile_direction_to_cardinal,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import VariantGeometryCatalog
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import BuildingConnectorSnapshot
from django_apps.asteroid_lab.optimization.coords import Coord


@dataclass(frozen=True, slots=True)
class CatalogOutputAttachment:
    output_stub_offset: Coord
    output_dir: str


def _is_output_connector_role(role: str) -> bool:
    normalized = role.strip().lower().replace("_", "")
    if normalized in ("output", "itemoutput", "buildingitemoutput"):
        return True
    return normalized.endswith("output") and "input" not in normalized


def _primary_output_connector(
    geometry: VariantGeometryCatalog,
) -> BuildingConnectorSnapshot | None:
    candidates: list[BuildingConnectorSnapshot] = []
    for connector in geometry.connectors:
        if _is_output_connector_role(connector.connector_role):
            candidates.append(connector)
    if not candidates:
        return None
    return min(candidates, key=lambda c: c.order_index)


def attachment_for_variant_rotation(
    geometry: VariantGeometryCatalog,
    rotation: CardinalDirection,
) -> CatalogOutputAttachment | None:
    primary = _primary_output_connector(geometry)
    if primary is None:
        return None
    try:
        base_dir = tile_direction_to_cardinal(primary.tile_direction)
    except CatalogTransformError:
        return None
    connector_local: Coord = (primary.position_x, primary.position_y)
    unit = cardinal_unit_vector(base_dir)
    base_stub = (connector_local[0] + unit[0], connector_local[1] + unit[1])
    stub_offset = rotate_coord(rotation, base_stub)
    rotated_dir = rotate_cardinal_direction(base_dir, rotation)
    try:
        occupied = expected_footprint_coords(
            geometry.footprint_cells,
            anchor_coord=(0, 0),
            rotation=rotation,
        )
    except CatalogTransformError:
        return None
    if stub_offset in occupied:
        return None
    return CatalogOutputAttachment(
        output_stub_offset=stub_offset,
        output_dir=rotated_dir.value,
    )


__all__ = ["CatalogOutputAttachment", "attachment_for_variant_rotation"]
