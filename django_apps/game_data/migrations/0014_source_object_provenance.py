# SourceObject auxiliary fields + nullable PROTECT FK on domain roots.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0013_simulation_multiple_belt_speed_cycle_ref"),
    ]

    operations = [
        migrations.AddField(
            model_name="sourceobject",
            name="source_path",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Auxiliary nested path (e.g. toolbar Children[]); not primary identity.",
                max_length=512,
            ),
        ),
        migrations.AddField(
            model_name="sourceobject",
            name="system_id",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="sourceobject",
            name="clr_type",
            field=models.CharField(blank=True, default="", max_length=512),
        ),
        migrations.AddField(
            model_name="buildingvariant",
            name="source_object",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="building_variants",
                to="game_data.sourceobject",
            ),
        ),
        migrations.AddField(
            model_name="buildinggroup",
            name="source_object",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="building_groups",
                to="game_data.sourceobject",
            ),
        ),
        migrations.AddField(
            model_name="gamecontentasset",
            name="source_object",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="content_assets",
                to="game_data.sourceobject",
            ),
        ),
        migrations.AddField(
            model_name="simulationsystem",
            name="source_object",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="simulation_systems",
                to="game_data.sourceobject",
            ),
        ),
        migrations.AddField(
            model_name="toolbartreenode",
            name="source_object",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="toolbar_tree_nodes",
                to="game_data.sourceobject",
            ),
        ),
        migrations.AddField(
            model_name="researchmilestone",
            name="source_object",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="research_milestones",
                to="game_data.sourceobject",
            ),
        ),
        migrations.AlterField(
            model_name="shaperecipe",
            name="source_object",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="shape_recipes",
                to="game_data.sourceobject",
            ),
        ),
    ]
