"""Shared fixtures for game_data unit tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from django_apps.game_data.importers import GameDataImporter
from django_apps.game_data.models import ImportBatch

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GAME_DATA_DIR = _REPO_ROOT / "documents" / "game_data"


def _flush_committed_game_data(django_db_blocker: Any) -> None:
    """Remove rows committed by module-scoped import (outside per-test rollback)."""
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


@pytest.fixture(scope="session")
def game_data_dir() -> Path:
    if not (_GAME_DATA_DIR / "manifest.json").is_file():
        pytest.skip("documents/game_data not present")
    return _GAME_DATA_DIR


@pytest.fixture
def imported_game_data_batch(game_data_dir: Path, db: None) -> ImportBatch:
    """Full manifest import inside the per-test transaction (isolated, repeatable)."""
    GameDataImporter(game_data_dir, batch_name="pytest-session").run()
    batch = ImportBatch.objects.order_by("-imported_at").first()
    assert batch is not None
    return batch


@pytest.fixture
def imported_batch(imported_game_data_batch: ImportBatch) -> ImportBatch:
    return imported_game_data_batch


@pytest.fixture(scope="module")
def imported_game_data_batch_module(
    game_data_dir: Path,
    django_db_setup: None,
    django_db_blocker,
) -> Iterator[ImportBatch]:
    """One full import per test module; tests only read imported ORM state."""
    with django_db_blocker.unblock():
        GameDataImporter(game_data_dir, batch_name="pytest-module").run()
        batch = ImportBatch.objects.order_by("-imported_at").first()
        assert batch is not None
    yield batch
    _flush_committed_game_data(django_db_blocker)


@pytest.fixture(scope="module")
def imported_batch_module(imported_game_data_batch_module: ImportBatch) -> ImportBatch:
    return imported_game_data_batch_module
