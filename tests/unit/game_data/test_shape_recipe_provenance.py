"""P1 provenance gates — ShapeRecipeSourceAppearance lineage."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.game_data.importers.source_loader import load_json
from django_apps.game_data.models import (
    ImportBatch,
    ShapeQuadrantSlot,
    ShapeRecipe,
    ShapeRecipeLayer,
    SourceObject,
)
from django_apps.game_data.models.shapes import ShapeRecipeSourceAppearance
from tests.unit.game_data._shape_json_helpers import count_layers_and_slots, shape_row_key


def test_shape_recipe_has_no_catalog_source_field() -> None:
    field_names = {f.name for f in ShapeRecipe._meta.get_fields()}
    assert "catalog_source" not in field_names


@pytest.fixture
def items_rows(game_data_dir: Path) -> list[dict]:
    return load_json(game_data_dir / "items.json")


def _overlap_keys(game_data_dir: Path) -> set[tuple[int, str]]:
    shapes = load_json(game_data_dir / "shapes.json")
    items = load_json(game_data_dir / "items.json")
    s_keys = {shape_row_key(r) for r in shapes}
    i_keys = {shape_row_key(r) for r in items}
    return {k for k in s_keys & i_keys if k[0] and k[1]}


@pytest.mark.django_db
def test_items_recipe_count_matches_source_appearances(
    imported_game_data_batch_module: ImportBatch,
    items_rows: list[dict],
) -> None:
    batch = imported_game_data_batch_module
    assert len(items_rows) == 70
    assert (
        ShapeRecipeSourceAppearance.objects.filter(
            import_batch=batch,
            catalog_source="items",
        ).count()
        == 70
    )


@pytest.mark.django_db
def test_shape_recipe_no_catalog_source_overwrite(
    imported_game_data_batch_module: ImportBatch,
    game_data_dir: Path,
) -> None:
    overlap = _overlap_keys(game_data_dir)
    if not overlap:
        pytest.skip("no FULL/ITEMS overlap in this dump")
    op_uid, shape_hash = next(iter(overlap))
    recipe = ShapeRecipe.objects.get(operation_uid=op_uid, shape_hash=shape_hash)
    apps = ShapeRecipeSourceAppearance.objects.filter(shape_recipe=recipe)
    assert apps.filter(catalog_source="full").exists()
    assert apps.filter(catalog_source="items").exists()


@pytest.mark.django_db
def test_shape_recipe_source_appearance_full_items_overlap(
    imported_game_data_batch_module: ImportBatch,
    game_data_dir: Path,
) -> None:
    overlap = _overlap_keys(game_data_dir)
    if not overlap:
        pytest.skip("no overlap")
    op_uid, shape_hash = next(iter(overlap))
    recipe = ShapeRecipe.objects.get(operation_uid=op_uid, shape_hash=shape_hash)
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
    items_rows: list[dict],
) -> None:
    batch = imported_game_data_batch_module
    for i, row in enumerate(items_rows):
        SourceObject.objects.get(
            import_batch=batch,
            source_file="items.json",
            source_row_index=i,
        )
        snap = row.get("definition_snapshot") or {}
        defn = snap.get("Definition") if isinstance(snap.get("Definition"), dict) else {}
        exp_layers, exp_slots = count_layers_and_slots(defn)
        appearance = ShapeRecipeSourceAppearance.objects.get(
            import_batch=batch,
            artifact_filename="items.json",
            source_row_index=i,
        )
        recipe = appearance.shape_recipe
        assert ShapeRecipeLayer.objects.filter(shape_recipe=recipe).count() == exp_layers
        assert ShapeQuadrantSlot.objects.filter(layer__shape_recipe=recipe).count() == exp_slots


def test_shape_recipe_items_keys_subset_of_shapes(game_data_dir: Path) -> None:
    """ITEMS rows reuse FULL keys; union has 70 duplicates, pair-UK still holds in DB."""
    shapes = load_json(game_data_dir / "shapes.json")
    items = load_json(game_data_dir / "items.json")
    shape_keys = {shape_row_key(r) for r in shapes}
    item_keys = {shape_row_key(r) for r in items}
    assert len(items) == 70
    assert item_keys <= shape_keys
    assert len(shape_keys) == 1170


@pytest.mark.django_db
def test_shape_recipe_count_matches_unique_pairs_after_import(
    imported_game_data_batch_module: ImportBatch,
    game_data_dir: Path,
) -> None:
    shapes = load_json(game_data_dir / "shapes.json")
    shape_keys = {shape_row_key(r) for r in shapes if shape_row_key(r)[0]}
    assert ShapeRecipe.objects.count() == len(shape_keys)


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
