"""Asteroid equipment placement projection — explicit layout allowlist + DB validation."""

from __future__ import annotations

from typing import Final

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    CatalogTransformError,
    expected_footprint_coords,
)
from django_apps.asteroid_lab.adapters.catalog_output_attachment import (
    attachment_for_variant_rotation,
)
from django_apps.asteroid_lab.catalog.island_extractor_defaults import (
    ISLAND_EXTRACTOR_DEFAULTS,
    IslandExtractorCarrierKind,
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
from django_apps.asteroid_lab.contracts.catalog_candidate import (
    catalog_pattern_id,
    throughput_factor_for_footprint,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind

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
        canonical_id=f"canon_manual:{layout}",
        internal_name=layout,
        footprint_cells=_MANUAL_FOOTPRINT,
        connectors=_MANUAL_CONNECTORS,
    )
    for layout in ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST
}


def _layouts_for_transport(transport_kind: TransportKind) -> frozenset[str]:
    return _LAYOUTS_BY_TRANSPORT.get(transport_kind, frozenset())


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
    throughput = throughput_factor_for_footprint(len(geometry.footprint_cells))
    specs: list[ProjectedEquipmentSpec] = []
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
            ProjectedEquipmentSpec(
                layout_t=geometry.internal_name,
                canonical_id=geometry.canonical_id,
                pattern_id=pattern_id,
                rotation=rotation,
                occupied_offsets=occupied,
                output_stub_offset=attachment.output_stub_offset,
                output_dir=CardinalDirection(attachment.output_dir),
                throughput_factor=throughput,
                source_kind=source_kind,
                source_detail=source_detail,
            )
        )
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
            key=lambda s: (s.canonical_id, s.rotation.value, s.pattern_id),
        )
    )


__all__ = [
    "ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST",
    "list_equipment_placement_specs",
]
