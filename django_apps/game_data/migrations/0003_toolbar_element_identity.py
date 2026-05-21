# Generated manually for toolbar identity boundary fix.

import re

import django.db.models.deletion
from django.db import migrations, models

_CHILD_INDEX_RE = re.compile(r"Children\[(\d+)\]$")


def _child_index(tree_path: str) -> int:
    match = _CHILD_INDEX_RE.search(tree_path)
    return int(match.group(1)) if match else 0


def backfill_island_placement_tree_paths(apps, schema_editor):
    ToolbarElement = apps.get_model("game_data", "ToolbarElement")
    ToolbarIslandPlacement = apps.get_model("game_data", "ToolbarIslandPlacement")

    for placement in ToolbarIslandPlacement.objects.select_related("toolbar_element").iterator():
        elem = placement.toolbar_element
        placement.tree_path = elem.tree_path
        placement.child_index = _child_index(placement.tree_path)
        placement.order_index = placement.child_index
        parts = placement.tree_path.split("/")
        if len(parts) >= 2:
            parent_path = "/".join(parts[:-1])
            parent = ToolbarElement.objects.filter(tree_path=parent_path).first()
            if parent:
                placement.parent_element_id = parent.pk
        placement.save(
            update_fields=["tree_path", "child_index", "order_index", "parent_element_id"]
        )

    for elem in ToolbarElement.objects.filter(element_kind="island").iterator():
        if elem.internal_name:
            continue
        placement = ToolbarIslandPlacement.objects.filter(toolbar_element_id=elem.pk).first()
        if placement:
            elem.internal_name = placement.island_group_name
            elem.save(update_fields=["internal_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0002_lazy_localized_text_refs"),
    ]

    operations = [
        migrations.AddField(
            model_name="toolbarelement",
            name="icon_identifier",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="toolbarelement",
            name="internal_name",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Stable domain key (e.g. island group name, building definition id).",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="toolbarelement",
            name="localized_title_key",
            field=models.CharField(blank=True, default="", max_length=512),
        ),
        migrations.AlterField(
            model_name="toolbarelement",
            name="tree_path",
            field=models.CharField(
                help_text="Import-only flatten locator (display_name_key).",
                max_length=512,
                unique=True,
            ),
        ),
        migrations.AlterModelOptions(
            name="toolbarelement",
            options={
                "ordering": ["internal_name", "source_row_index"],
                "verbose_name": "toolbar element",
                "verbose_name_plural": "⑦ Toolbar · Elements",
            },
        ),
        migrations.AddField(
            model_name="toolbarislandplacement",
            name="child_index",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="toolbarislandplacement",
            name="order_index",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="toolbarislandplacement",
            name="parent_element",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="island_placement_children",
                to="game_data.toolbarelement",
            ),
        ),
        migrations.AddField(
            model_name="toolbarislandplacement",
            name="tree_path",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Flattened JSON tree locator (display_name_key); debug/audit only.",
                max_length=512,
            ),
        ),
        migrations.RunPython(backfill_island_placement_tree_paths, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="toolbarislandplacement",
            name="tree_path",
            field=models.CharField(
                help_text="Flattened JSON tree locator (display_name_key); debug/audit only.",
                max_length=512,
                unique=True,
            ),
        ),
        migrations.AlterModelOptions(
            name="toolbarislandplacement",
            options={
                "ordering": ["tree_path"],
                "verbose_name": "toolbar island placement",
                "verbose_name_plural": "⑦ Toolbar · Island placements",
            },
        ),
    ]
