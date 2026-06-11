"""Load ``SpaceTransportTileCatalog`` — DB registry first, JSON dump fallback."""

from __future__ import annotations

import logging
from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from django_apps.asteroid_lab.services.space_transport_catalog_import import (
    import_space_transport_catalog_from_game_data,
)
from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
    SpaceTransportCatalogInvalid,
    SpaceTransportTileCatalog,
)

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_JSON_SOURCE_CANDIDATES: tuple[Path, ...] = (
    _REPO_ROOT / "documents" / "game_data",
    _REPO_ROOT / "documents" / "knowledge" / "raw" / "game_data",
)

_last_catalog_load_source: str | None = None


class SpaceTransportCatalogLoadSource(StrEnum):
    DB = "db"
    JSON_FALLBACK = "json_fallback"


class SpaceTransportCatalogUnavailable(Exception):
    """Raised when neither ORM registry nor raw JSON catalog can be resolved."""


def get_last_space_transport_catalog_load_source() -> str | None:
    return _last_catalog_load_source


def _set_last_catalog_load_source(source: str | None) -> None:
    global _last_catalog_load_source
    _last_catalog_load_source = source


def _resolve_json_source_dir() -> Path | None:
    for candidate in _JSON_SOURCE_CANDIDATES:
        research = candidate / "research_unlocks.json"
        simulation = candidate / "simulation_systems.json"
        if research.is_file() and simulation.is_file():
            return candidate
    return None


def _load_catalog_from_db() -> SpaceTransportTileCatalog | None:
    from django_apps.game_data.services.space_transport_layout_catalog import (
        build_space_transport_catalog_payload_from_orm,
    )

    payload = build_space_transport_catalog_payload_from_orm()
    if payload is None:
        return None
    return SpaceTransportTileCatalog.from_payload(payload)


def _load_catalog_from_json(*, source_dir: Path) -> SpaceTransportTileCatalog:
    payload = import_space_transport_catalog_from_game_data(
        research_unlocks_path=source_dir / "research_unlocks.json",
        simulation_systems_path=source_dir / "simulation_systems.json",
    )
    return SpaceTransportTileCatalog.from_payload(payload)


def load_space_transport_catalog(*, prefer_db: bool = True) -> SpaceTransportTileCatalog:
    """Resolve island transport catalog; DB registry is authoritative when present."""

    if prefer_db:
        try:
            catalog = _load_catalog_from_db()
        except SpaceTransportCatalogInvalid as exc:
            msg = f"invalid space transport layout rows in database: {exc}"
            raise SpaceTransportCatalogUnavailable(msg) from exc
        if catalog is not None:
            _set_last_catalog_load_source(SpaceTransportCatalogLoadSource.DB.value)
            return catalog

    source_dir = _resolve_json_source_dir()
    if source_dir is not None:
        try:
            catalog = _load_catalog_from_json(source_dir=source_dir)
        except (OSError, SpaceTransportCatalogInvalid, ValueError, TypeError) as exc:
            msg = f"json fallback failed under {source_dir}: {exc}"
            raise SpaceTransportCatalogUnavailable(msg) from exc
        _set_last_catalog_load_source(SpaceTransportCatalogLoadSource.JSON_FALLBACK.value)
        logger.warning(
            "space_transport_catalog_json_fallback",
            extra={
                "source_dir": str(source_dir),
                "reason": "SpaceTransportLayoutRegistry empty; using raw game_data JSON",
            },
        )
        return catalog

    raise SpaceTransportCatalogUnavailable(
        "no SpaceTransportLayoutRegistry rows and no research_unlocks/simulation_systems JSON"
    )


@lru_cache(maxsize=1)
def _cached_load_space_transport_catalog(prefer_db: bool) -> SpaceTransportTileCatalog:
    return load_space_transport_catalog(prefer_db=prefer_db)


def try_load_space_transport_catalog_from_snapshot(
    payload: dict[str, object],
) -> SpaceTransportTileCatalog | None:
    """Build catalog from ``game_data_snapshot.space_transport_layouts`` (closed-world)."""

    layouts = payload.get("space_transport_layouts")
    if not isinstance(layouts, list) or not layouts:
        return None
    from django_apps.game_data.services.space_transport_layout_catalog import (
        build_space_transport_catalog_payload_from_snapshot_layouts,
    )

    try:
        catalog_payload = build_space_transport_catalog_payload_from_snapshot_layouts(layouts)
    except ValueError:
        return None
    return SpaceTransportTileCatalog.from_payload(catalog_payload)


def try_load_default_space_transport_catalog() -> SpaceTransportTileCatalog | None:
    """Soft loader for optional catalog consumers (returns None instead of raising)."""

    try:
        return _cached_load_space_transport_catalog(prefer_db=True)
    except SpaceTransportCatalogUnavailable:
        return None


def clear_space_transport_catalog_loader_cache() -> None:
    _cached_load_space_transport_catalog.cache_clear()
    _set_last_catalog_load_source(None)


__all__ = [
    "SpaceTransportCatalogLoadSource",
    "SpaceTransportCatalogUnavailable",
    "clear_space_transport_catalog_loader_cache",
    "get_last_space_transport_catalog_load_source",
    "load_space_transport_catalog",
    "try_load_default_space_transport_catalog",
    "try_load_space_transport_catalog_from_snapshot",
]
