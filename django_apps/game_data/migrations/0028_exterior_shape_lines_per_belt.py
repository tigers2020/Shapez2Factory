# EVTC — Asteroid Lab exterior connector sizing (12 lines × 720/min per Space Belt).

from __future__ import annotations

from django.db import migrations, models


def backfill_shape_lines_per_belt(apps, schema_editor) -> None:
    Shape = apps.get_model("game_data", "ExteriorShapeTransportCapacity")
    Shape.objects.filter(speed_tier=1, is_active=True).update(
        lanes_per_line=12,
        lines_per_space_belt=12,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0027_exterior_transport_capacity_tier1"),
    ]

    operations = [
        migrations.AddField(
            model_name="exteriorshapetransportcapacity",
            name="lanes_per_line",
            field=models.PositiveSmallIntegerField(default=12),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="exteriorshapetransportcapacity",
            name="lines_per_space_belt",
            field=models.PositiveSmallIntegerField(default=12),
            preserve_default=False,
        ),
        migrations.RunPython(
            backfill_shape_lines_per_belt,
            migrations.RunPython.noop,
        ),
    ]
