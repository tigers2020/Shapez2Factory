"""Normalize cutter_full → cutter; drop CUTTER_FULL from MacroRecipeStep choices."""

from django.db import migrations, models


def forwards(apps, schema_editor):
    MacroRecipeStep = apps.get_model("shapez_solver", "MacroRecipeStep")
    MacroRecipeStep.objects.filter(operation="cutter_full").update(operation="cutter")

    MacroRecipe = apps.get_model("shapez_solver", "MacroRecipe")
    for mr in MacroRecipe.objects.exclude(graph_document__isnull=True):
        doc = mr.graph_document
        if not isinstance(doc, dict):
            continue
        nodes = doc.get("nodes")
        if not isinstance(nodes, list):
            continue
        changed = False
        for node in nodes:
            if isinstance(node, dict) and node.get("operation") == "cutter_full":
                node["operation"] = "cutter"
                changed = True
        if changed:
            mr.save(update_fields=["graph_document"])


def backwards(apps, schema_editor):
    pass


_OPERATION_CHOICES = [
    ("cutter", "CUTTER"),
    ("half_destroyer", "HALF_DESTROYER"),
    ("splitter", "SPLITTER"),
    ("swapper", "SWAPPER"),
    ("rotate_cw", "ROTATE_CW"),
    ("rotate_ccw", "ROTATE_CCW"),
    ("rotate_180", "ROTATE_180"),
    ("stacker", "STACKER"),
    ("painter", "PAINTER"),
    ("color_mixer", "COLOR_MIXER"),
    ("pin_pusher", "PIN_PUSHER"),
    ("crystal_generator", "CRYSTAL_GENERATOR"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("shapez_solver", "0004_patternfamily_graph_draft"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name="macrorecipestep",
            name="operation",
            field=models.CharField(
                choices=_OPERATION_CHOICES,
                max_length=32,
                verbose_name="작업",
            ),
        ),
    ]
