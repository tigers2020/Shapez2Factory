"""Tier A supplement for ``SpaceTransportLayoutRegistry`` in pytest (Tier B dump gap)."""

from __future__ import annotations

import os
from datetime import UTC, datetime

from django_apps.game_data.importers.base import ImportContext
from django_apps.game_data.importers.source_loader import load_json
from django_apps.game_data.importers.space_transport_layouts import import_space_transport_layouts
from django_apps.game_data.models import ImportBatch, SpaceTransportLayoutRegistry
from django_apps.game_data.services.space_transport_layout_catalog import (
    EXPECTED_SPACE_TRANSPORT_LAYOUT_COUNT,
)
from tests.unit.game_data.dump_paths import resolve_game_data_source_dir

_PYTEST_LAYOUT_SEED_BATCH = "pytest-tier-a-space-layout-seed"
_PYTEST_LAYOUT_SEED_HASH = "sha256:pytest-tier-a-space-layout-seed"


def _pytest_layout_seed_batch() -> ImportBatch:
    source = resolve_game_data_source_dir()
    if source is None:
        msg = "Tier A game_data bundle not found for pytest layout seed batch"
        raise RuntimeError(msg)
    manifest_data = load_json(source / "manifest.json")
    return ImportBatch.objects.get_or_create(
        manifest_self_hash=_PYTEST_LAYOUT_SEED_HASH,
        defaults={
            "batch_name": _PYTEST_LAYOUT_SEED_BATCH,
            "game_version": str(manifest_data.get("game_version", "")),
            "unity_version": str(manifest_data.get("unity_version", "")),
            "dump_mod_version": str(manifest_data.get("dump_mod_version", "")),
            "dump_schema_version": str(manifest_data.get("dump_schema_version", "")),
            "dump_timestamp_utc": datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC),
            "source_method": "pytest_layout_seed",
        },
    )[0]


def ensure_space_transport_layout_registry(
    batch: ImportBatch | None = None,
    *,
    strict: bool = False,
) -> None:
    """Import 54 layouts from Tier A when the registry is empty or short."""

    if SpaceTransportLayoutRegistry.objects.count() >= EXPECTED_SPACE_TRANSPORT_LAYOUT_COUNT:
        return

    source = resolve_game_data_source_dir()
    if source is None:
        if strict or os.environ.get("CI") or os.environ.get("REQUIRE_GAME_DATA_DUMP") == "1":
            msg = (
                "SpaceTransportLayoutRegistry short and Tier A game_data bundle not found "
                "for supplement import"
            )
            raise RuntimeError(msg)
        return

    seed_batch = batch or _pytest_layout_seed_batch()
    manifest_data = load_json(source / "manifest.json")
    import_space_transport_layouts(
        ImportContext(seed_batch),
        research_unlocks_path=source / "research_unlocks.json",
        simulation_systems_path=source / "simulation_systems.json",
        game_version=str(manifest_data.get("game_version", "")),
    )
    count = SpaceTransportLayoutRegistry.objects.count()
    if count != EXPECTED_SPACE_TRANSPORT_LAYOUT_COUNT:
        msg = (
            f"expected {EXPECTED_SPACE_TRANSPORT_LAYOUT_COUNT} SpaceTransportLayoutRegistry rows "
            f"after supplement import, got {count}"
        )
        raise RuntimeError(msg)


__all__ = ["ensure_space_transport_layout_registry"]
