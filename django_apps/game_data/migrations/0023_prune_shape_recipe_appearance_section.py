# Recipe appearances are inline under ShapeRecipe — no standalone browse section.

from django.db import migrations

SUBTABLE = "game_data.ShapeRecipeSourceAppearance"


def prune_section(apps, schema_editor) -> None:
    Section = apps.get_model("game_data", "GameDataSection")
    Section.objects.filter(django_model_label=SUBTABLE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0022_remove_shaperecipe_catalog_source"),
    ]

    operations = [
        migrations.RunPython(prune_section, migrations.RunPython.noop),
    ]
