"""Port for Layer 04 space belt/pipe tile catalog (no raw game JSON in core L4)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
        SpaceTransportTileCatalogEntry,
    )


class SpaceTransportCatalogPort(Protocol):
    def lookup_io(
        self,
        *,
        transport_kind: str,
        input_mask: tuple[bool, bool, bool, bool],
        output_mask: tuple[bool, bool, bool, bool],
    ) -> SpaceTransportTileCatalogEntry:
        """Resolve tile by ESWN I/O signature at R0_E_CW."""
        ...

    def lookup_tile_id(self, tile_id: str) -> SpaceTransportTileCatalogEntry:
        """Resolve tile by island layout id (``SpaceBelt_Forward``, etc.)."""
        ...


__all__ = ["SpaceTransportCatalogPort"]
