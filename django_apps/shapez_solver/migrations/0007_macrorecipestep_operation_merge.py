"""Add merge to MacroRecipeStep.operation choices."""

from django.db import migrations, models

_OPERATION_CHOICES = [
    ("cutter", "CUTTER"),
    ("half_destroyer", "HALF_DESTROYER"),
    ("splitter", "SPLITTER"),
    ("swapper", "SWAPPER"),
    ("rotate_cw", "ROTATE_CW"),
    ("rotate_ccw", "ROTATE_CCW"),
    ("rotate_180", "ROTATE_180"),
    ("stacker", "STACKER"),
    ("merge", "MERGE"),
    ("painter", "PAINTER"),
    ("color_mixer", "COLOR_MIXER"),
    ("pin_pusher", "PIN_PUSHER"),
    ("crystal_generator", "CRYSTAL_GENERATOR"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("shapez_solver", "0006_seed_pattern_catalog"),
    ]

    operations = [
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
