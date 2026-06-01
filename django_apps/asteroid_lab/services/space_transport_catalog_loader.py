"""Load ``SpaceTransportTileCatalog`` from repo game_data (Django boundary only)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from django_apps.asteroid_lab.services.space_transport_catalog_import import (
    import_space_transport_catalog_from_game_data,
)
from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
    SpaceTransportCatalogInvalid,
    SpaceTransportTileCatalog,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_RESEARCH = _REPO_ROOT / "documents" / "game_data" / "research_unlocks.json"
_DEFAULT_SIMULATION = _REPO_ROOT / "documents" / "game_data" / "simulation_systems.json"


@lru_cache(maxsize=1)
def try_load_default_space_transport_catalog() -> SpaceTransportTileCatalog | None:
    """Return catalog from default game_data paths, or None if import fails."""

    if not _DEFAULT_RESEARCH.is_file() or not _DEFAULT_SIMULATION.is_file():
        return None
    try:
        payload = import_space_transport_catalog_from_game_data(
            research_unlocks_path=_DEFAULT_RESEARCH,
            simulation_systems_path=_DEFAULT_SIMULATION,
        )
        return SpaceTransportTileCatalog.from_payload(payload)
    except (OSError, SpaceTransportCatalogInvalid, ValueError, TypeError):
        return None


__all__ = ["try_load_default_space_transport_catalog"]
