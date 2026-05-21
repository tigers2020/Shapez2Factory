# ruff: noqa: E501

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0016_admin_taxonomy"),
    ]

    operations = [
        migrations.CreateModel(
            name="GameDataReference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ref_kind", models.CharField(choices=[("building_variant", "Building variant"), ("building_group", "Building group"), ("research_mechanic", "Research mechanic"), ("research_upgrade", "Research upgrade"), ("shape_recipe", "Shape recipe"), ("content_asset", "Content asset"), ("simulation_system", "Simulation system"), ("toolbar_node", "Toolbar node"), ("other", "Other")], max_length=128)),
                ("ref_value", models.CharField(max_length=512)),
                ("resolved", models.BooleanField(default=False)),
                (
                    "from_source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outgoing_references",
                        to="game_data.sourceobject",
                    ),
                ),
                (
                    "import_batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="data_references",
                        to="game_data.importbatch",
                    ),
                ),
                (
                    "to_source",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="incoming_references",
                        to="game_data.sourceobject",
                    ),
                ),
            ],
            options={
                "verbose_name": "unresolved reference",
                "verbose_name_plural": "⑪ References · Unresolved",
            },
        ),
        migrations.AddIndex(
            model_name="gamedatareference",
            index=models.Index(fields=["import_batch", "ref_kind", "resolved"], name="gd_ref_batch_kind_res"),
        ),
    ]
