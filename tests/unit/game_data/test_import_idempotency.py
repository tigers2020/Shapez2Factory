"""Importer idempotency against documents/game_data."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.game_data.importers import GameDataImporter
from django_apps.game_data.models import (
    BuildingVariant,
    FluidColor,
    GameContentAsset,
    ImportBatch,
    ShapeRecipe,
)


@pytest.fixture
def game_data_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "documents" / "game_data"
    if not (root / "manifest.json").is_file():
        pytest.skip("documents/game_data not present")
    return root


def _model_counts() -> dict[str, int]:
    return {
        "import_batch": ImportBatch.objects.count(),
        "fluid_color": FluidColor.objects.count(),
        "shape_recipe": ShapeRecipe.objects.count(),
        "building_variant": BuildingVariant.objects.count(),
        "content_asset": GameContentAsset.objects.count(),
    }


@pytest.mark.django_db
def test_import_is_idempotent(game_data_dir: Path) -> None:
    importer = GameDataImporter(game_data_dir, batch_name="pytest")
    importer.run()
    first = _model_counts()
    first_batch_hash = ImportBatch.objects.get().manifest_self_hash
    importer.run()
    second = _model_counts()
    assert first == second
    assert ImportBatch.objects.count() == 1
    assert ImportBatch.objects.get().manifest_self_hash == first_batch_hash
