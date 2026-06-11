"""Shared fixtures for game_data unit tests (Tier B pinned dump)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command

from django_apps.game_data.importers.base import ImportContext
from django_apps.game_data.importers.source_loader import load_json
from django_apps.game_data.importers.space_transport_layouts import import_space_transport_layouts
from django_apps.game_data.models import ImportBatch, SpaceTransportLayoutRegistry
from django_apps.game_data.models.exterior_transport_capacity import (
    ExteriorFluidTransportCapacity,
    ExteriorShapeTransportCapacity,
)
from django_apps.game_data.models.mining import MiningExtractionRule
from django_apps.game_data.services.space_transport_layout_catalog import (
    EXPECTED_SPACE_TRANSPORT_LAYOUT_COUNT,
)
from tests.unit.game_data._dump_expectations import (
    PINNED_BATCH_NAME,
    PINNED_IMPORT_BATCH_PK,
    PINNED_MANIFEST_HASH,
)
from tests.unit.game_data.dump_paths import (
    resolve_game_data_dump_path,
    resolve_game_data_source_dir,
)


def _require_game_data_dump() -> Path:
    path = resolve_game_data_dump_path()
    if path is not None:
        return path
    if os.environ.get("CI") or os.environ.get("REQUIRE_GAME_DATA_DUMP") == "1":
        pytest.fail(
            "Missing pinned game_data dump (checked canon and documents/knowledge/raw paths)"
        )
    pytest.skip(
        "Missing pinned game_data dump (checked canon and documents/knowledge/raw paths)"
    )


def _supplement_space_transport_layouts(batch: ImportBatch) -> None:
    """Tier B dump predates SpaceTransportLayoutRegistry; import from Tier A when short."""

    if SpaceTransportLayoutRegistry.objects.count() >= EXPECTED_SPACE_TRANSPORT_LAYOUT_COUNT:
        return
    source = resolve_game_data_source_dir()
    if source is None:
        if os.environ.get("CI") or os.environ.get("REQUIRE_GAME_DATA_DUMP") == "1":
            pytest.fail(
                "Pinned dump missing SpaceTransportLayoutRegistry rows and Tier A game_data "
                "bundle not found for supplement import"
            )
        pytest.skip("Tier A game_data bundle not present for space transport layout supplement")
    manifest_data = load_json(source / "manifest.json")
    import_space_transport_layouts(
        ImportContext(batch),
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
        pytest.fail(msg)


_FLUSH_SKIP_TABLES = frozenset(
    {
        MiningExtractionRule._meta.db_table,
        ExteriorShapeTransportCapacity._meta.db_table,
        ExteriorFluidTransportCapacity._meta.db_table,
    }
)


def _flush_committed_game_data(django_db_blocker: Any) -> None:
    """Delete imported game_data rows (module teardown / pre-loaddata). Never global flush.

    CANON tables seeded by migration (MiningExtractionRule, Exterior*TransportCapacity)
    are preserved ??not loaddata.
    """
    from django.apps import apps
    from django.db import connection

    tables = [
        model._meta.db_table
        for model in apps.get_app_config("game_data").get_models()
        if model._meta.db_table not in _FLUSH_SKIP_TABLES
    ]
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            if connection.vendor == "sqlite":
                cursor.execute("PRAGMA foreign_keys = OFF")
            for table in tables:
                cursor.execute(f'DELETE FROM "{table}"')
            if connection.vendor == "sqlite":
                cursor.execute("PRAGMA foreign_keys = ON")


def _assert_pinned_import_batch() -> ImportBatch:
    batch = ImportBatch.objects.get(pk=PINNED_IMPORT_BATCH_PK)
    assert batch.batch_name == PINNED_BATCH_NAME
    assert batch.manifest_self_hash == PINNED_MANIFEST_HASH
    return batch


@pytest.fixture(scope="module")
def game_data_dump_path() -> Path:
    return _require_game_data_dump()


@pytest.fixture(scope="module")
def imported_game_data_batch_module(
    game_data_dump_path: Path,
    django_db_setup: None,
    django_db_blocker,
) -> Iterator[ImportBatch]:
    """One loaddata per test module; app-local flush only (no global flush)."""
    with django_db_blocker.unblock():
        _flush_committed_game_data(django_db_blocker)
        call_command("loaddata", str(game_data_dump_path), verbosity=0)
        batch = _assert_pinned_import_batch()
        _supplement_space_transport_layouts(batch)
    yield batch
    _flush_committed_game_data(django_db_blocker)


@pytest.fixture
def imported_game_data_batch(
    imported_game_data_batch_module: ImportBatch,
    db: None,
) -> ImportBatch:
    return imported_game_data_batch_module


@pytest.fixture
def imported_batch(imported_game_data_batch: ImportBatch) -> ImportBatch:
    return imported_game_data_batch


@pytest.fixture(scope="module")
def imported_batch_module(imported_game_data_batch_module: ImportBatch) -> ImportBatch:
    return imported_game_data_batch_module
