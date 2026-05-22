"""Shared fixtures for game_data unit tests (Tier B pinned dump)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command

from django_apps.game_data.models import ImportBatch
from tests.unit.game_data._dump_expectations import (
    PINNED_BATCH_NAME,
    PINNED_IMPORT_BATCH_PK,
    PINNED_MANIFEST_HASH,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GAME_DATA_DUMP = _REPO_ROOT / "game_data_backup" / "game_data_dump.json"


def _require_game_data_dump(path: Path) -> None:
    if path.is_file():
        return
    if os.environ.get("CI") or os.environ.get("REQUIRE_GAME_DATA_DUMP") == "1":
        pytest.fail(f"Missing pinned game_data dump: {path}")
    pytest.skip(f"Missing pinned game_data dump: {path}")


def _flush_committed_game_data(django_db_blocker: Any) -> None:
    """Delete all game_data app rows (module teardown / pre-loaddata). Never global flush."""
    from django.apps import apps
    from django.db import connection

    tables = [model._meta.db_table for model in apps.get_app_config("game_data").get_models()]
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
    _require_game_data_dump(_GAME_DATA_DUMP)
    return _GAME_DATA_DUMP


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
