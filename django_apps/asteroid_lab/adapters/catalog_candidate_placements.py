"""Build catalog-native placement specs from BuildingCatalogSlice (Track D+ PR-3)."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    CatalogTransformError,
    expected_footprint_coords,
)
from django_apps.asteroid_lab.adapters.catalog_output_attachment import (
    attachment_for_variant_rotation,
)
from django_apps.asteroid_lab.adapters.catalog_transport_policy import (
    canonical_ids_for_transport_kind,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.contracts.catalog_candidate import (
    CatalogPlacementSpec,
    catalog_pattern_id,
    throughput_factor_for_footprint,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind

_CARDINAL_ORDER: tuple[CardinalDirection, ...] = (
    CardinalDirection.E,
    CardinalDirection.N,
    CardinalDirection.S,
    CardinalDirection.W,
)


def build_catalog_placement_specs(
    catalog_slice: BuildingCatalogSlice,
    *,
    transport_kind: TransportKind,
) -> tuple[CatalogPlacementSpec, ...]:
    allowed = canonical_ids_for_transport_kind(catalog_slice, transport_kind)
    specs: list[CatalogPlacementSpec] = []
    for geometry in catalog_slice.variant_geometries:
        if geometry.canonical_id not in allowed:
            continue
        if not geometry.footprint_cells:
            continue
        throughput = throughput_factor_for_footprint(len(geometry.footprint_cells))
        for rotation in _CARDINAL_ORDER:
            try:
                occupied = expected_footprint_coords(
                    geometry.footprint_cells,
                    anchor_coord=(0, 0),
                    rotation=rotation,
                )
            except CatalogTransformError:
                continue
            attachment = attachment_for_variant_rotation(geometry, rotation)
            if attachment is None:
                continue
            pattern_id = catalog_pattern_id(geometry.canonical_id, rotation)
            specs.append(
                CatalogPlacementSpec(
                    canonical_id=geometry.canonical_id,
                    rotation=rotation,
                    pattern_id=pattern_id,
                    occupied_offsets=occupied,
                    output_stub_offset=attachment.output_stub_offset,
                    output_dir=attachment.output_dir,
                    throughput_factor=throughput,
                )
            )
    return tuple(sorted(specs, key=lambda s: (s.canonical_id, s.rotation.value, s.pattern_id)))


__all__ = ["build_catalog_placement_specs"]
