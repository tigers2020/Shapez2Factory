# ShapeRecipeSourceAppearance (P1 provenance) + backfill from deprecated catalog_source.

from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


def backfill_shape_recipe_appearances(apps, schema_editor) -> None:
    ShapeRecipe = apps.get_model("game_data", "ShapeRecipe")
    ShapeRecipeSourceAppearance = apps.get_model("game_data", "ShapeRecipeSourceAppearance")
    for recipe in ShapeRecipe.objects.select_related("source_object").iterator():
        if recipe.source_object_id is None:
            continue
        src = recipe.source_object
        filename = "shapes.json" if recipe.catalog_source == "full" else "items.json"
        ShapeRecipeSourceAppearance.objects.get_or_create(
            import_batch_id=recipe.import_batch_id,
            artifact_filename=filename,
            source_row_index=src.source_row_index,
            defaults={
                "shape_recipe_id": recipe.pk,
                "source_object_id": src.pk,
                "catalog_source": recipe.catalog_source,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0020_merge_20260521_1757"),
    ]

    operations = [
        migrations.CreateModel(
            name="ShapeRecipeSourceAppearance",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "catalog_source",
                    models.CharField(
                        choices=[
                            ("full", "shapes.json"),
                            ("items", "items.json subset"),
                        ],
                        max_length=16,
                    ),
                ),
                ("artifact_filename", models.CharField(max_length=64)),
                ("source_row_index", models.PositiveIntegerField()),
                (
                    "import_batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shape_recipe_appearances",
                        to="game_data.importbatch",
                    ),
                ),
                (
                    "shape_recipe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="source_appearances",
                        to="game_data.shaperecipe",
                    ),
                ),
                (
                    "source_object",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="shape_recipe_appearances",
                        to="game_data.sourceobject",
                    ),
                ),
            ],
            options={
                "verbose_name": "shape recipe source appearance",
                "verbose_name_plural": "③ Shapes · Recipe appearances",
                "ordering": ["artifact_filename", "source_row_index"],
            },
        ),
        migrations.AddConstraint(
            model_name="shaperecipesourceappearance",
            constraint=models.UniqueConstraint(
                fields=("import_batch", "artifact_filename", "source_row_index"),
                name="uq_shape_appearance_batch_file_row",
            ),
        ),
        migrations.RunPython(backfill_shape_recipe_appearances, migrations.RunPython.noop),
    ]
