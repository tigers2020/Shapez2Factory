"""T1 default transport resolution from ``BuildingCatalogSlice`` (Track B2)."""

from __future__ import annotations

from enum import StrEnum

from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


class CatalogTransportErrorCode(StrEnum):
    CATALOG_TRANSPORT_UNRESOLVED = "catalog_transport_unresolved"


class CatalogTransportUnresolvedError(Exception):
    def __init__(self, code: CatalogTransportErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)


# Observed ``transport_category`` values on registry rows (game_data import).
_TRANSPORT_CATEGORY_TO_KIND: dict[str, TransportKind] = {
    "belt": TransportKind.SHAPE_BELT,
    "pipe": TransportKind.FLUID_PIPE,
}


def resolve_default_asteroid_transport_kind(
    catalog_slice: BuildingCatalogSlice,
) -> TransportKind:
    """T1 policy: asteroid greenfield default is shape belt when catalog has a belt channel.

    Pipe registry rows do not compete for asteroid default (belt + pipe in DB is OK).
    Fail-closed only when no belt-category row classifies to ``SHAPE_BELT``.
    Never uses registry tuple order.
    """

    has_belt_channel = False
    for entry in catalog_slice.transport_registry:
        category = entry.transport_category.strip().lower()
        if _TRANSPORT_CATEGORY_TO_KIND.get(category) is TransportKind.SHAPE_BELT:
            has_belt_channel = True
            break
    if has_belt_channel:
        return TransportKind.SHAPE_BELT
    raise CatalogTransportUnresolvedError(
        CatalogTransportErrorCode.CATALOG_TRANSPORT_UNRESOLVED,
        "cannot resolve default asteroid transport from catalog registry",
    )


def transport_kind_lookup_from_slice(
    catalog_slice: BuildingCatalogSlice,
) -> dict[str, TransportKind]:
    """Map game-data registry ``transport_kind`` keys to domain ``TransportKind``."""

    lookup: dict[str, TransportKind] = {}
    for entry in catalog_slice.transport_registry:
        category = entry.transport_category.strip().lower()
        kind = _TRANSPORT_CATEGORY_TO_KIND.get(category)
        if kind is None:
            continue
        key = entry.transport_kind
        existing = lookup.get(key)
        if existing is not None and existing is not kind:
            raise CatalogTransportUnresolvedError(
                CatalogTransportErrorCode.CATALOG_TRANSPORT_UNRESOLVED,
                (
                    f"conflicting transport_kind registry key {key!r}: "
                    f"{existing.value!r} vs {kind.value!r}"
                ),
            )
        lookup[key] = kind
    return lookup


def resolve_cell_transport_kind(
    raw: str,
    *,
    catalog_slice: BuildingCatalogSlice | None,
    lookup: dict[str, TransportKind] | None = None,
    coord: tuple[int, int] | None = None,
) -> TransportKind | None:
    """Resolve one cell wire string; RTTP callers pass ``catalog_slice``."""

    for member in TransportKind:
        if member.value == raw:
            return member
    if catalog_slice is None:
        return None
    table = lookup if lookup is not None else transport_kind_lookup_from_slice(catalog_slice)
    mapped = table.get(raw)
    if mapped is not None:
        return mapped
    where = f" at coord {coord!r}" if coord is not None else ""
    raise CatalogTransportUnresolvedError(
        CatalogTransportErrorCode.CATALOG_TRANSPORT_UNRESOLVED,
        f"cannot resolve transport_kind wire {raw!r}{where} from catalog registry",
    )


def canonical_ids_for_transport_kind(
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


__all__ = [
    "CatalogTransportErrorCode",
    "CatalogTransportUnresolvedError",
    "canonical_ids_for_transport_kind",
    "resolve_cell_transport_kind",
    "resolve_default_asteroid_transport_kind",
    "transport_kind_lookup_from_slice",
]
