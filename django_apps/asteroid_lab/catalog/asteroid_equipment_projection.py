"""Asteroid equipment placement projection — explicit layout allowlist + DB validation."""

from __future__ import annotations

from typing import Final

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import cardinal_unit_vector
from django_apps.asteroid_lab.catalog.extension_topology_synthesis import (
    synthesize_opposite_arm_linear_topologies,
)
from django_apps.asteroid_lab.catalog.island_extractor_defaults import (
    ISLAND_EXTRACTOR_DEFAULTS,
    IslandExtractorCarrierKind,
)
from django_apps.asteroid_lab.catalog.miner_placement_topology import (
    MinerPlacementTopology,
    normalize_miner_placement_topology,
)
from django_apps.asteroid_lab.catalog.projection_source import (
    ProjectedEquipmentSpec,
    ProjectionSourceKind,
    is_factory_internal_variant,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
    VariantGeometryCatalog,
)
from django_apps.asteroid_lab.contracts.catalog_candidate import catalog_pattern_id
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
)
from django_apps.asteroid_lab.genetic_sample.gene_template import (
    throughput_factor_for_extension_count,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind

CANON_MANUAL_CANONICAL_ID_PREFIX: Final[str] = "canon_manual:"

ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "Layout_ShapeMiner",
        "Layout_FluidMiner",
    }
)

_LAYOUTS_BY_TRANSPORT: Final[dict[TransportKind, frozenset[str]]] = {
    TransportKind.SHAPE_BELT: frozenset({"Layout_ShapeMiner"}),
    TransportKind.FLUID_PIPE: frozenset({"Layout_FluidMiner"}),
}

_CARDINAL_ORDER: Final[tuple[CardinalDirection, ...]] = (
    CardinalDirection.E,
    CardinalDirection.N,
    CardinalDirection.S,
    CardinalDirection.W,
)

_MANUAL_FOOTPRINT: Final[tuple[BuildingFootprintCell, ...]] = (
    BuildingFootprintCell(x=0, y=0, order_index=0),
    BuildingFootprintCell(x=1, y=0, order_index=1),
)

_MANUAL_CONNECTORS: Final[tuple[BuildingConnectorSnapshot, ...]] = (
    BuildingConnectorSnapshot(0, "output", "East", "Regular", 1, 0, 0),
)

_MANUAL_GEOMETRY_BY_LAYOUT: Final[dict[str, VariantGeometryCatalog]] = {
    layout: VariantGeometryCatalog(
        canonical_id=f"{CANON_MANUAL_CANONICAL_ID_PREFIX}{layout}",
        internal_name=layout,
        footprint_cells=_MANUAL_FOOTPRINT,
        connectors=_MANUAL_CONNECTORS,
    )
    for layout in ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST
}


def _layouts_for_transport(transport_kind: TransportKind) -> frozenset[str]:
    return _LAYOUTS_BY_TRANSPORT.get(transport_kind, frozenset())


def _violates_inv_r(
    topo: MinerPlacementTopology,
    extension_offsets: tuple[Coord, ...],
    *,
    output_dir: CardinalDirection,
) -> bool:
    occupied = frozenset({topo.extractor_offset, *extension_offsets})
    if topo.fixed_output_transport_offset in occupied:
        return True
    if topo.output_stub_offset in occupied:
        return True
    unit = cardinal_unit_vector(output_dir)
    output_axis = (
        topo.extractor_offset[0] + unit[0],
        topo.extractor_offset[1] + unit[1],
    )
    return output_axis in extension_offsets


def _projected_spec_for_extension_count(
    geometry: VariantGeometryCatalog,
    topo: MinerPlacementTopology,
    *,
    rotation: CardinalDirection,
    extension_offsets: tuple[Coord, ...],
    extension_count: int,
    topology_kind: str,
    source_kind: ProjectionSourceKind,
    source_detail: str,
) -> ProjectedEquipmentSpec | None:
    if _violates_inv_r(topo, extension_offsets, output_dir=rotation):
        return None
    occupied = frozenset({topo.extractor_offset, *extension_offsets})
    return ProjectedEquipmentSpec(
        layout_t=geometry.internal_name,
        canonical_id=geometry.canonical_id,
        pattern_id=catalog_pattern_id(
            geometry.canonical_id,
            rotation,
            extension_count=extension_count,
        ),
        rotation=rotation,
        extractor_offset=topo.extractor_offset,
        extension_offsets=extension_offsets,
        fixed_output_transport_offset=topo.fixed_output_transport_offset,
        output_stub_offset=topo.output_stub_offset,
        occupied_offsets=tuple(sorted(occupied)),
        output_dir=CardinalDirection(topo.output_dir),
        throughput_factor=throughput_factor_for_extension_count(extension_count),
        topology_kind=topology_kind,
        source_kind=source_kind,
        source_detail=source_detail,
    )


def _specs_from_geometry(
    geometry: VariantGeometryCatalog,
    *,
    source_kind: ProjectionSourceKind,
    source_detail: str,
) -> list[ProjectedEquipmentSpec]:
    if not geometry.footprint_cells:
        return []
    if is_factory_internal_variant(geometry.internal_name):
        return []
    specs: list[ProjectedEquipmentSpec] = []
    for rotation in _CARDINAL_ORDER:
        topo = normalize_miner_placement_topology(geometry, rotation)
        if topo is None:
            continue
        for ext_topo in synthesize_opposite_arm_linear_topologies(output_dir=rotation):
            row = _projected_spec_for_extension_count(
                geometry,
                topo,
                rotation=rotation,
                extension_offsets=ext_topo.extension_offsets,
                extension_count=ext_topo.extension_count,
                topology_kind=ext_topo.topology_kind.value,
                source_kind=source_kind,
                source_detail=source_detail,
            )
            if row is not None:
                specs.append(row)
    return specs


def _manual_specs_for_layout(
    layout_t: str,
    *,
    transport_kind: TransportKind,
) -> list[ProjectedEquipmentSpec]:
    geometry = _MANUAL_GEOMETRY_BY_LAYOUT[layout_t]
    variant_keys = [
        row.variant_key.value
        for row in ISLAND_EXTRACTOR_DEFAULTS
        if row.layout_t == layout_t
        and (
            row.carrier_kind is IslandExtractorCarrierKind.SHAPE
            if transport_kind is TransportKind.SHAPE_BELT
            else row.carrier_kind is IslandExtractorCarrierKind.FLUID
        )
    ]
    detail = f"island:{','.join(variant_keys) or layout_t}"
    return _specs_from_geometry(
        geometry,
        source_kind=ProjectionSourceKind.CANON_MANUAL,
        source_detail=detail,
    )


def list_equipment_placement_specs(
    catalog_slice: BuildingCatalogSlice,
    *,
    transport_kind: TransportKind,
) -> tuple[ProjectedEquipmentSpec, ...]:
    """Placement specs for asteroid miners/extensions (never factory InternalVariant belts)."""

    layouts = _layouts_for_transport(transport_kind)
    if not layouts:
        return ()

    specs: list[ProjectedEquipmentSpec] = []
    seen_layouts: set[str] = set()

    for geometry in catalog_slice.variant_geometries:
        if geometry.internal_name not in ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST:
            continue
        if geometry.internal_name not in layouts:
            continue
        rows = _specs_from_geometry(
            geometry,
            source_kind=ProjectionSourceKind.GAME_DATA_CANON,
            source_detail=f"batch_slice:{catalog_slice.slice_version}",
        )
        if rows:
            seen_layouts.add(geometry.internal_name)
            specs.extend(rows)

    for layout_t in sorted(layouts):
        if layout_t in seen_layouts:
            continue
        specs.extend(_manual_specs_for_layout(layout_t, transport_kind=transport_kind))

    return tuple(
        sorted(
            specs,
            key=lambda s: (
                s.canonical_id,
                s.rotation.value,
                s.pattern_id,
            ),
        )
    )


__all__ = [
    "ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST",
    "CANON_MANUAL_CANONICAL_ID_PREFIX",
    "list_equipment_placement_specs",
]
