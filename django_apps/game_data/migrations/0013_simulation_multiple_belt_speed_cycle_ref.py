# MultipleBeltSpeed: persist BaseSpeed.$cycle ref for audit when FK alone is ambiguous.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0012_simulation_typed_speed_tables"),
    ]

    operations = [
        migrations.AddField(
            model_name="simulationmultiplebeltspeed",
            name="cycle_ref_type",
            field=models.CharField(
                blank=True,
                default="",
                help_text="``BaseSpeed.$cycle`` target (e.g. BuffableBeltSpeed).",
                max_length=64,
            ),
        ),
    ]
