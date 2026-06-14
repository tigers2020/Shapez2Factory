# EVTC tier-1 — Shapez 2 1.0 mini miner / inner belt / Space Belt rates (30·16·480·12).

from __future__ import annotations

from decimal import Decimal

from django.db import migrations, models

EVTC_SPEC = "documents/superpowers/specs/2026-05-26-rttp-external-void-transport-capacity-contract.md"


def correct_tier1_shape_transport_rates(apps, schema_editor) -> None:
    Shape = apps.get_model("game_data", "ExteriorShapeTransportCapacity")
    Shape.objects.filter(speed_tier=1, is_active=True).update(
        mini_unit_output_per_min=Decimal("30.0000"),
        buildings_per_regular_belt=4,
        miner_full_output_multiplier=16,
        lanes_per_line=12,
        lines_per_space_belt=12,
        space_belt_full_belt_count=48,
        source_note=(
            "Shapez 2 1.0 tier-1: mini 30/min; expander x16 → 480/min line; "
            "inner belt 120/min (4×30); 12 inner belts export; "
            "Space Belt 480/min × 12 lines = 5760/min per building. EVTC spec: " + EVTC_SPEC
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0028_exterior_shape_lines_per_belt"),
    ]

    operations = [
        migrations.AddField(
            model_name="exteriorshapetransportcapacity",
            name="miner_full_output_multiplier",
            field=models.PositiveSmallIntegerField(default=16),
            preserve_default=False,
        ),
        migrations.RunPython(
            correct_tier1_shape_transport_rates,
            migrations.RunPython.noop,
        ),
    ]
