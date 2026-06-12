"""Shared fixtures for game_data unit tests (Tier B pinned dump)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from django.core.management import call_command

from django_apps.game_data.models import ImportBatch
from django_apps.game_data.models.exterior_transport_capacity import (
    ExteriorFluidTransportCapacity,
    ExteriorShapeTransportCapacity,
)
from django_apps.game_data.models.mining import MiningExtractionRule
from tests.support.game_data_layout_seed import ensure_space_transport_layout_registry
from tests.unit.game_data._dump_expectations import (
    PINNED_BATCH_NAME,
    PINNED_IMPORT_BATCH_PK,
    PINNED_MANIFEST_HASH,
)
from tests.unit.game_data.dump_paths import resolve_game_data_dump_path


def _require_game_data_dump() -> Path:
    path = resolve_game_data_dump_path()
    if path is not None:
        return path
    if os.environ.get("CI") or os.environ.get("REQUIRE_GAME_DATA_DUMP") == "1":
        pytest.fail(
            "Missing pinned game_data dump (checked canon and documents/knowledge/raw paths)"
        )
    pytest.skip("Missing pinned game_data dump (checked canon and documents/knowledge/raw paths)")


def _supplement_space_transport_layouts(batch: ImportBatch) -> None:
    """Tier B dump predates SpaceTransportLayoutRegistry; import from Tier A when short."""

    try:
        ensure_space_transport_layout_registry(batch=batch, strict=True)
    except RuntimeError as exc:
        if os.environ.get("CI") or os.environ.get("REQUIRE_GAME_DATA_DUMP") == "1":
            pytest.fail(str(exc))
        pytest.skip(str(exc))


_FLUSH_SKIP_TABLES = frozenset(
    {
        MiningExtractionRule._meta.db_table,
        ExteriorShapeTransportCapacity._meta.db_table,
        ExteriorFluidTransportCapacity._meta.db_table,
    }
)


def _flush_committed_game_data(django_db_blocker: object) -> None:
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
