"""Asteroid transport placement projection — registry filtering and route tile synthesis."""

from __future__ import annotations

from typing import Final

from django_apps.asteroid_lab.catalog.projection_source import (
    COMPAT_TRANSPORT_STUB_FOOTPRINT,
    ProjectedTransportTile,
    ProjectionSourceKind,
    is_factory_internal_variant,  # re-export for transport policy tests
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind

# Mirrors ``catalog_transport_policy`` registry classification (catalog stays adapter-free).
_TRANSPORT_CATEGORY_TO_KIND: Final[dict[str, TransportKind]] = {
    "belt": TransportKind.SHAPE_BELT,
    "pipe": TransportKind.FLUID_PIPE,
}

_ROUTE_DETAIL_FORWARD: Final[str] = "compat:route_forward"
_ROUTE_DETAIL_LEFT: Final[str] = "compat:route_left_turn"
_ROUTE_DETAIL_RIGHT: Final[str] = "compat:route_right_turn"
_ROUTE_DETAIL_FORWARD_FALLBACK: Final[str] = "compat:route_forward_fallback"


def _registry_canonical_ids_for_transport_kind(
    catalog_slice: BuildingCatalogSlice,
    transport_kind: TransportKind,
) -> frozenset[str]:
    out: set[str] = set()
    for entry in catalog_slice.transport_registry:
        category = entry.transport_category.strip().lower()
        mapped = _TRANSPORT_CATEGORY_TO_KIND.get(category)
        if mapped is transport_kind:
            out.add(entry.building_variant_canonical_id)
    return frozenset(out)


def placement_transport_canonical_ids(
    catalog_slice: BuildingCatalogSlice,
    transport_kind: TransportKind,
) -> frozenset[str]:
    """Placement allowlist: registry IDs for ``transport_kind`` minus InternalVariant."""

    internal_by_cid: dict[str, str] = {
        v.canonical_id: v.internal_name for v in catalog_slice.variants
    }
    allowed: set[str] = set()
    for cid in _registry_canonical_ids_for_transport_kind(catalog_slice, transport_kind):
        internal_name = internal_by_cid.get(cid)
        if internal_name is not None and is_factory_internal_variant(internal_name):
            continue
        allowed.add(cid)
    return frozenset(allowed)


def _transport_sprite_prefix(transport_kind: TransportKind) -> str:
    return "SpacePipe" if transport_kind is TransportKind.FLUID_PIPE else "SpaceBelt"


def _route_segment_layout_t(
    incoming: int | None,
    outgoing: int | None,
    *,
    sprite_prefix: str,
) -> tuple[str, int, str]:
    """Map prev/current/next flow dirs to East-canonical belt/pipe sprite (PR-1b).

    Dir ints: 0=E, 1=S, 2=W, 3=N. Returns ``(layout_t, display_rotation_q, source_detail)``.
    """

    if incoming is None and outgoing is None:
        return f"{sprite_prefix}_Forward", 0, _ROUTE_DETAIL_FORWARD
    if incoming is None:
        assert outgoing is not None
        return f"{sprite_prefix}_Forward", outgoing, _ROUTE_DETAIL_FORWARD
    if outgoing is None:
        return f"{sprite_prefix}_Forward", incoming, _ROUTE_DETAIL_FORWARD
    if incoming == outgoing:
        return f"{sprite_prefix}_Forward", outgoing, _ROUTE_DETAIL_FORWARD
    if (incoming + 2) % 4 == outgoing:
        return f"{sprite_prefix}_Forward", outgoing, _ROUTE_DETAIL_FORWARD
    if (incoming + 1) % 4 == outgoing:
        return f"{sprite_prefix}_RightTurn", 0, _ROUTE_DETAIL_RIGHT
    if (incoming + 3) % 4 == outgoing:
        return f"{sprite_prefix}_LeftTurn", 0, _ROUTE_DETAIL_LEFT
    return f"{sprite_prefix}_Forward", outgoing, _ROUTE_DETAIL_FORWARD_FALLBACK


def resolve_route_tile(
    *,
    transport_kind: TransportKind,
    incoming_dir: int | None,
    outgoing_dir: int | None,
) -> ProjectedTransportTile:
    """PR-1b turn/forward synthesis (dirs 0=E, 1=S, 2=W, 3=N).

    Phase A uses ``TEMPORARY_COMPAT`` until game_data carries Space* route rows.
    """

    sprite_prefix = _transport_sprite_prefix(transport_kind)
    layout_t, display_rotation_q, source_detail = _route_segment_layout_t(
        incoming_dir,
        outgoing_dir,
        sprite_prefix=sprite_prefix,
    )
    tile = ProjectedTransportTile(
        layout_t=layout_t,
        transport_kind=transport_kind,
        canonical_id=None,
        footprint_cells=COMPAT_TRANSPORT_STUB_FOOTPRINT,
        display_rotation_q=display_rotation_q,
        source_kind=ProjectionSourceKind.TEMPORARY_COMPAT,
        source_detail=source_detail,
    )
    from django_apps.asteroid_lab.catalog.projection_compat_metrics import (
        record_route_compat_tile_emitted,
    )

    record_route_compat_tile_emitted()
    return tile


__all__ = [
    "is_factory_internal_variant",
    "placement_transport_canonical_ids",
    "resolve_route_tile",
]
