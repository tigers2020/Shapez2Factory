"""Shared fixtures for game_data unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.game_data.importers import GameDataImporter
from django_apps.game_data.models import ImportBatch

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GAME_DATA_DIR = _REPO_ROOT / "documents" / "game_data"


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
) -> ImportBatch:
    """One full import per test module; tests only read imported ORM state."""
    with django_db_blocker.unblock():
        GameDataImporter(game_data_dir, batch_name="pytest-module").run()
        batch = ImportBatch.objects.order_by("-imported_at").first()
        assert batch is not None
    return batch


@pytest.fixture(scope="module")
def imported_batch_module(imported_game_data_batch_module: ImportBatch) -> ImportBatch:
    return imported_game_data_batch_module
