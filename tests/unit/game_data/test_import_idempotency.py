"""Importer idempotency against documents/game_data."""

from __future__ import annotations

import pytest

from django_apps.game_data.importers import GameDataImporter
from django_apps.game_data.models import (
    BuildingVariant,
    FluidColor,
    GameContentAsset,
    ImportBatch,
    ShapeRecipe,
    SimulationSystem,
)


def _model_counts() -> dict[str, int]:
    return {
        "import_batch": ImportBatch.objects.count(),
        "fluid_color": FluidColor.objects.count(),
        "shape_recipe": ShapeRecipe.objects.count(),
        "building_variant": BuildingVariant.objects.count(),
        "content_asset": GameContentAsset.objects.count(),
        "simulation_system": SimulationSystem.objects.count(),
    }


@pytest.mark.django_db
def test_import_is_idempotent(game_data_dir: Path) -> None:
    """Full manifest re-import is idempotent (see also per-slice re-import tests)."""
    batch_name = "pytest-idempotency"
    importer = GameDataImporter(game_data_dir, batch_name=batch_name)
    importer.run()
    first = _model_counts()
    first_batch_hash = ImportBatch.objects.get(batch_name=batch_name).manifest_self_hash
    batch_rows = ImportBatch.objects.filter(batch_name=batch_name).count()
    importer.run()
    second = _model_counts()
    assert first == second
    assert ImportBatch.objects.filter(batch_name=batch_name).count() == batch_rows
    assert ImportBatch.objects.get(batch_name=batch_name).manifest_self_hash == first_batch_hash
