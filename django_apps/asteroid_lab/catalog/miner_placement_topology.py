"""Normalize catalog miner footprints to GeneTemplate-aligned topology (Phase 1)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    CatalogTransformError,
    cardinal_unit_vector,
    expected_footprint_coords,
)
from django_apps.asteroid_lab.adapters.catalog_output_attachment import (
    attachment_for_variant_rotation,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import VariantGeometryCatalog
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.genetic_sample.gene_template import (
    throughput_factor_for_extension_count,
)
from django_apps.asteroid_lab.optimization.coords import Coord


@dataclass(frozen=True, slots=True)
class MinerPlacementTopology:
    canonical_id: str
    rotation: CardinalDirection
    extractor_offset: Coord
    extension_offsets: tuple[Coord, ...]
    fixed_output_transport_offset: Coord
    output_stub_offset: Coord
    output_dir: str
    throughput_factor: int
    footprint_evidence: frozenset[Coord]

    @property
    def occupied_offsets(self) -> frozenset[Coord]:
        return frozenset({self.extractor_offset}) | frozenset(self.extension_offsets)


def _resolve_extractor_offset(
    footprint_evidence: frozenset[Coord],
    fixed_output_transport_offset: Coord,
    *,
    explicit_catalog_anchor: Coord | None,
) -> Coord | None:
    candidates = footprint_evidence - {fixed_output_transport_offset}
    if len(candidates) == 1:
        return next(iter(candidates))
    if explicit_catalog_anchor is not None and explicit_catalog_anchor in candidates:
        return explicit_catalog_anchor
    return None


def normalize_miner_placement_topology(
    geometry: VariantGeometryCatalog,
    rotation: CardinalDirection,
    *,
    explicit_catalog_anchor: Coord | None = None,
) -> MinerPlacementTopology | None:
    attachment = attachment_for_variant_rotation(geometry, rotation)
    if attachment is None:
        return None
    try:
        footprint_evidence = expected_footprint_coords(
            geometry.footprint_cells,
            anchor_coord=(0, 0),
            rotation=rotation,
        )
    except CatalogTransformError:
        return None
    output_dir = CardinalDirection(attachment.output_dir)
    unit = cardinal_unit_vector(output_dir)
    output_stub_offset = attachment.output_stub_offset
    fixed_output_transport_offset = (
        output_stub_offset[0] - unit[0],
        output_stub_offset[1] - unit[1],
    )
    extractor_offset = _resolve_extractor_offset(
        footprint_evidence,
        fixed_output_transport_offset,
        explicit_catalog_anchor=explicit_catalog_anchor,
    )
    if extractor_offset is None:
        return None
    if extractor_offset != (0, 0):
        return None
    extension_offsets: tuple[Coord, ...] = ()
    occupied = frozenset({extractor_offset}) | frozenset(extension_offsets)
    if fixed_output_transport_offset in occupied:
        return None
    if output_stub_offset in occupied:
        return None
    output_axis = (extractor_offset[0] + unit[0], extractor_offset[1] + unit[1])
    if output_axis in extension_offsets:
        return None
    if output_stub_offset != (
        fixed_output_transport_offset[0] + unit[0],
        fixed_output_transport_offset[1] + unit[1],
    ):
        return None
    throughput_factor = throughput_factor_for_extension_count(len(extension_offsets))
    return MinerPlacementTopology(
        canonical_id=geometry.canonical_id,
        rotation=rotation,
        extractor_offset=extractor_offset,
        extension_offsets=extension_offsets,
        fixed_output_transport_offset=fixed_output_transport_offset,
        output_stub_offset=output_stub_offset,
        output_dir=output_dir.value,
        throughput_factor=throughput_factor,
        footprint_evidence=footprint_evidence,
    )


__all__ = ["MinerPlacementTopology", "normalize_miner_placement_topology"]
