# ToolbarTreeNode hierarchy; remove ToolbarTreeEdge; reshape ToolbarElement / IslandPlacement.

import django.db.models.deletion
from django.db import migrations, models


def clear_toolbar_tables(apps, schema_editor):
    for name in (
        "ToolbarIslandPlacement",
        "ToolbarBuildingPlacement",
        "ToolbarTreeEdge",
        "ToolbarElement",
    ):
        apps.get_model("game_data", name).objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0003_toolbar_element_identity"),
    ]

    operations = [
        migrations.RunPython(clear_toolbar_tables, migrations.RunPython.noop),
        migrations.CreateModel(
            name="ToolbarTreeNode",
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
                ("canonical_id", models.CharField(max_length=255, unique=True)),
                ("source_stable_id", models.CharField(blank=True, default="", max_length=64)),
                ("child_index", models.PositiveSmallIntegerField(default=0)),
                ("order_index", models.PositiveSmallIntegerField(default=0)),
                ("depth", models.PositiveSmallIntegerField(default=0)),
                (
                    "node_kind",
                    models.CharField(
                        choices=[
                            ("root", "Root"),
                            ("folder", "Folder / category"),
                            ("group", "Group"),
                            ("separator", "Separator"),
                            ("action", "Action"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "tree_path",
                    models.CharField(
                        db_index=True,
                        help_text="Flattened display_name_key from dump; debug/audit only.",
                        max_length=512,
                    ),
                ),
                ("internal_name", models.CharField(blank=True, default="", max_length=255)),
                ("localized_title_key", models.CharField(blank=True, default="", max_length=512)),
                ("icon_identifier", models.CharField(blank=True, default="", max_length=255)),
                ("source_row_index", models.PositiveIntegerField()),
                (
                    "import_batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="toolbar_tree_nodes",
                        to="game_data.importbatch",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="children",
                        to="game_data.toolbartreenode",
                    ),
                ),
            ],
            options={
                "verbose_name": "toolbar tree node",
                "verbose_name_plural": "⑦ Toolbar · Tree nodes",
                "ordering": ["depth", "child_index"],
            },
        ),
        migrations.AddConstraint(
            model_name="toolbartreenode",
            constraint=models.UniqueConstraint(
                fields=("parent", "child_index"),
                name="uq_toolbar_node_sibling",
            ),
        ),
        migrations.DeleteModel(
            name="ToolbarTreeEdge",
        ),
        migrations.RemoveField(
            model_name="toolbarislandplacement",
            name="child_index",
        ),
        migrations.RemoveField(
            model_name="toolbarislandplacement",
            name="order_index",
        ),
        migrations.RemoveField(
            model_name="toolbarislandplacement",
            name="parent_element",
        ),
        migrations.RemoveField(
            model_name="toolbarislandplacement",
            name="tree_path",
        ),
        migrations.AddField(
            model_name="toolbarelement",
            name="display_name",
            field=models.CharField(blank=True, default="", max_length=512),
        ),
        migrations.AddField(
            model_name="toolbarelement",
            name="stable_key",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="toolbarelement",
            name="tree_node",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="toolbar_element",
                to="game_data.toolbartreenode",
            ),
        ),
        migrations.AlterField(
            model_name="toolbarelement",
            name="source_stable_id",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.RemoveField(
            model_name="toolbarelement",
            name="icon_identifier",
        ),
        migrations.RemoveField(
            model_name="toolbarelement",
            name="internal_name",
        ),
        migrations.RemoveField(
            model_name="toolbarelement",
            name="localized_title_key",
        ),
        migrations.RemoveField(
            model_name="toolbarelement",
            name="tree_path",
        ),
        migrations.AlterModelOptions(
            name="toolbarelement",
            options={
                "ordering": ["display_name", "source_row_index"],
                "verbose_name": "toolbar element",
                "verbose_name_plural": "⑦ Toolbar · Elements",
            },
        ),
        migrations.AlterModelOptions(
            name="toolbarislandplacement",
            options={
                "ordering": ["island_group_name"],
                "verbose_name": "toolbar island placement",
                "verbose_name_plural": "⑦ Toolbar · Island placements",
            },
        ),
    ]
