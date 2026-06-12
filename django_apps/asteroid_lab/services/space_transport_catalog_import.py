"""Import island SpaceBelt/SpacePipe catalog from ``documents/game_data`` JSON dumps."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shapez2_factory.adapters.game_data.space_transport_layout_extract import (
    build_space_transport_catalog_payload,
)


def import_space_transport_catalog_from_game_data(
    *,
    research_unlocks_path: str | Path,
    simulation_systems_path: str | Path,
    game_version: str = "",
) -> dict[str, Any]:
    """Build a catalog payload suitable for ``SpaceTransportTileCatalog.from_payload``."""
    return build_space_transport_catalog_payload(
        research_unlocks_path=research_unlocks_path,
        simulation_systems_path=simulation_systems_path,
        game_version=game_version,
    )


__all__ = [
    "build_space_transport_catalog_payload",
    "import_space_transport_catalog_from_game_data",
]
