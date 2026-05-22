"""Web assembler for AsteroidGameDataSnapshot."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab.optimization.game_data_contracts import SCHEMA_VERSION
from django_apps.game_data.importers import GameDataImporter
from django_apps.game_data.selectors.import_batch import pin_latest_import_batch


def _game_data_dir() -> Path:
    root = Path(__file__).resolve().parents[3]
    data_dir = root / "documents" / "game_data"
    if not (data_dir / "manifest.json").is_file():
        pytest.skip("documents/game_data not present")
    return data_dir


@pytest.mark.django_db
@pytest.mark.slow
def test_assemble_snapshot_matches_pinned_revision() -> None:
    from django_apps.web.services.asteroid_game_data_snapshot import (
        build_asteroid_game_data_snapshot,
    )

    GameDataImporter(_game_data_dir(), batch_name="pytest-web-assembler").run()
    batch = pin_latest_import_batch()
    snap = build_asteroid_game_data_snapshot()

    assert snap.meta.schema_version == SCHEMA_VERSION
    assert snap.meta.data_revision == batch.manifest_self_hash
    assert snap.meta.content_hash
    assert len(snap.meta.content_hash) == 64
    assert snap.buildings
    assert snap.transport_registry
    building_names = [b.internal_name for b in snap.buildings]
    assert building_names == sorted(building_names)
