import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0014_source_object_provenance"),
    ]

    operations = [
        migrations.AddField(
            model_name="toolbartreenode",
            name="required_mechanic",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="toolbar_tree_nodes",
                to="game_data.researchmechanic",
            ),
        ),
        migrations.AddField(
            model_name="toolbartreenode",
            name="icon_content_asset",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="toolbar_nodes_by_icon",
                to="game_data.gamecontentasset",
            ),
        ),
    ]
