"""FK cross-references from audit graph."""

from __future__ import annotations

import pytest

from django_apps.game_data.models import (
    ImportBatch,
    AssetMetaReference,
    ResearchUnlockCost,
    ToolbarBuildingPlacement,
    ToolbarIslandPlacement,
)


@pytest.mark.django_db
def test_toolbar_building_placement_resolves_variant(
    imported_game_data_batch: ImportBatch,
) -> None:
    del imported_game_data_batch
    placements = ToolbarBuildingPlacement.objects.select_related("building_variant")
    assert placements.exists()
    for row in placements[:5]:
        assert row.building_variant_id is not None
        assert row.building_variant.internal_name == row.building_definition_key


@pytest.mark.django_db
def test_asset_meta_links_content(imported_game_data_batch: ImportBatch) -> None:
    del imported_game_data_batch
    assert AssetMetaReference.objects.exists()
    for meta in AssetMetaReference.objects.select_related("content_asset")[:10]:
        assert meta.content_asset_id is not None


@pytest.mark.django_db
def test_island_placement_placer_id_populated(imported_game_data_batch: ImportBatch) -> None:
    del imported_game_data_batch
    assert ToolbarIslandPlacement.objects.count() == 63
    assert ToolbarIslandPlacement.objects.filter(placer_id="").count() == 0


@pytest.mark.django_db
def test_research_cost_links_shape_recipe(imported_game_data_batch: ImportBatch) -> None:
    del imported_game_data_batch
    costs = ResearchUnlockCost.objects.select_related("shape_recipe")
    if not costs.exists():
        pytest.skip("no research costs resolved in this dump")
    for cost in costs[:10]:
        assert cost.shape_recipe.shape_hash
