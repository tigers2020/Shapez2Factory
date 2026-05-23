"""P1 provenance gates ??ShapeRecipeSourceAppearance lineage."""

from __future__ import annotations

import pytest
from django.db import models

from django_apps.game_data.models import (
    ImportBatch,
    ShapeQuadrantSlot,
    ShapeRecipe,
    ShapeRecipeLayer,
)
from django_apps.game_data.models.shapes import ShapeRecipeSourceAppearance
from tests.unit.game_data._dump_expectations import (
    ITEMS_SOURCE_APPEARANCE_COUNT,
    SHAPE_RECIPE_COUNT,
)


def test_shape_recipe_has_no_catalog_source_field() -> None:
    field_names = {f.name for f in ShapeRecipe._meta.get_fields()}
    assert "catalog_source" not in field_names


def _recipe_with_full_and_items_sources(batch: ImportBatch) -> ShapeRecipe:
    overlap_ids = (
        ShapeRecipeSourceAppearance.objects.filter(import_batch=batch)
        .values("shape_recipe_id")
        .annotate(n=models.Count("catalog_source", distinct=True))
        .filter(n__gte=2)
        .order_by("shape_recipe_id")
    )
    first = overlap_ids.first()
    assert first is not None
    return ShapeRecipe.objects.get(pk=first["shape_recipe_id"])


@pytest.mark.django_db
def test_items_recipe_count_matches_pinned_dump(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    batch = imported_game_data_batch_module
    assert (
        ShapeRecipeSourceAppearance.objects.filter(
            import_batch=batch,
            catalog_source="items",
        ).count()
        == ITEMS_SOURCE_APPEARANCE_COUNT
    )


@pytest.mark.django_db
def test_shape_recipe_no_catalog_source_overwrite(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    batch = imported_game_data_batch_module
    recipe = _recipe_with_full_and_items_sources(batch)
    apps = ShapeRecipeSourceAppearance.objects.filter(shape_recipe=recipe)
    assert apps.filter(catalog_source="full").exists()
    assert apps.filter(catalog_source="items").exists()


@pytest.mark.django_db
def test_shape_recipe_source_appearance_full_items_overlap(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    batch = imported_game_data_batch_module
    recipe = _recipe_with_full_and_items_sources(batch)
    sources = set(
        ShapeRecipeSourceAppearance.objects.filter(shape_recipe=recipe).values_list(
            "catalog_source",
            flat=True,
        )
    )
    assert sources == {"full", "items"}


@pytest.mark.django_db
def test_items_layer_slot_parity_by_source_object(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    batch = imported_game_data_batch_module
    appearances = ShapeRecipeSourceAppearance.objects.filter(
        import_batch=batch,
        catalog_source="items",
    )
    assert appearances.count() == ITEMS_SOURCE_APPEARANCE_COUNT
    for appearance in appearances:
        recipe = appearance.shape_recipe
        layer_count = ShapeRecipeLayer.objects.filter(shape_recipe=recipe).count()
        slot_count = ShapeQuadrantSlot.objects.filter(layer__shape_recipe=recipe).count()
        assert layer_count > 0
        assert slot_count > 0


@pytest.mark.django_db
def test_shape_recipe_count_matches_pinned_dump(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    assert ShapeRecipe.objects.count() == SHAPE_RECIPE_COUNT


@pytest.mark.django_db
def test_shape_recipe_db_distinct_pairs_match_row_count(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    """Pre/post pair-UK: distinct (operation_uid, shape_hash) == row count."""
    del imported_game_data_batch_module
    total = ShapeRecipe.objects.count()
    distinct_pairs = ShapeRecipe.objects.values("operation_uid", "shape_hash").distinct().count()
    assert total == distinct_pairs
    assert total > 0
