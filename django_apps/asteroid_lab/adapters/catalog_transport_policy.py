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


__all__ = [
    "CatalogTransportErrorCode",
    "CatalogTransportUnresolvedError",
    "resolve_default_asteroid_transport_kind",
]
