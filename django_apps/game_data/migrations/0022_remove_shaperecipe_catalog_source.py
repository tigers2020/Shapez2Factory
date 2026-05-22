# Phase 1d: catalog lineage only on ShapeRecipeSourceAppearance.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0021_shape_recipe_source_appearance"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="shaperecipe",
            name="catalog_source",
        ),
    ]
