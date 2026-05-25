"""Build catalog-native placement specs from equipment projection (Phase A)."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import cardinal_unit_vector
from django_apps.asteroid_lab.catalog.asteroid_equipment_projection import (
    list_equipment_placement_specs,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.contracts.catalog_candidate import CatalogPlacementSpec
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def _fixed_output_transport_offset(output_dir: str, output_stub_offset: Coord) -> Coord:
    """INV-R-05: FOT is one cell before output stub along output_dir."""

    unit = cardinal_unit_vector(CardinalDirection(output_dir))
    return (output_stub_offset[0] - unit[0], output_stub_offset[1] - unit[1])


def build_catalog_placement_specs(
    catalog_slice: BuildingCatalogSlice,
    *,
    transport_kind: TransportKind,
) -> tuple[CatalogPlacementSpec, ...]:
    projected = list_equipment_placement_specs(catalog_slice, transport_kind=transport_kind)
    specs: list[CatalogPlacementSpec] = []
    for row in projected:
        output_dir = row.output_dir.value
        output_stub_offset = row.output_stub_offset
        specs.append(
            CatalogPlacementSpec(
                canonical_id=row.canonical_id,
                rotation=row.rotation,
                pattern_id=row.pattern_id,
                occupied_offsets=frozenset(row.occupied_offsets),
                fixed_output_transport_offset=_fixed_output_transport_offset(
                    output_dir,
                    output_stub_offset,
                ),
                output_stub_offset=output_stub_offset,
                output_dir=output_dir,
                throughput_factor=row.throughput_factor,
            )
        )
    return tuple(specs)


__all__ = ["build_catalog_placement_specs"]
