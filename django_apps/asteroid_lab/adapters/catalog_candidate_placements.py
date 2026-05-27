"""Build catalog-native placement specs from equipment projection (Phase A)."""

from __future__ import annotations

from django_apps.asteroid_lab.catalog.asteroid_equipment_projection import (
    list_equipment_placement_specs,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.contracts.catalog_candidate import CatalogPlacementSpec
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def build_catalog_placement_specs(
    catalog_slice: BuildingCatalogSlice,
    *,
    transport_kind: TransportKind,
) -> tuple[CatalogPlacementSpec, ...]:
    projected = list_equipment_placement_specs(catalog_slice, transport_kind=transport_kind)
    specs: list[CatalogPlacementSpec] = []
    for row in projected:
        specs.append(
            CatalogPlacementSpec(
                canonical_id=row.canonical_id,
                rotation=row.rotation,
                pattern_id=row.pattern_id,
                extractor_offset=row.extractor_offset,
                extension_offsets=row.extension_offsets,
                fixed_output_transport_offset=row.fixed_output_transport_offset,
                output_stub_offset=row.output_stub_offset,
                occupied_offsets=frozenset(row.occupied_offsets),
                output_dir=row.output_dir.value,
                throughput_factor=row.throughput_factor,
                topology_kind=row.topology_kind,
            )
        )
    return tuple(specs)


__all__ = ["build_catalog_placement_specs"]
