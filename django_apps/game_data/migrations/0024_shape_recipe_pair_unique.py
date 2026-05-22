# Canonical ShapeRecipe identity: (operation_uid, shape_hash) pair unique.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0023_prune_shape_recipe_appearance_section"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shaperecipe",
            name="operation_uid",
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name="shaperecipe",
            name="shape_hash",
            field=models.CharField(max_length=128),
        ),
        migrations.AddConstraint(
            model_name="shaperecipe",
            constraint=models.UniqueConstraint(
                fields=("operation_uid", "shape_hash"),
                name="uq_shape_recipe_op_uid_hash",
            ),
        ),
    ]
