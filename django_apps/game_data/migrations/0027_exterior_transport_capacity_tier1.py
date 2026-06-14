# Generated for EVTC-1a — Shapez 2 1.0 tier-1 exterior transport CANON rows.

from __future__ import annotations

from decimal import Decimal

from django.db import migrations, models

EVTC_SPEC = (
    "documents/superpowers/specs/" "2026-05-26-rttp-external-void-transport-capacity-contract.md"
)


def seed_exterior_transport_capacity_tier1(apps, schema_editor) -> None:
    Shape = apps.get_model("game_data", "ExteriorShapeTransportCapacity")
    Fluid = apps.get_model("game_data", "ExteriorFluidTransportCapacity")

    Shape.objects.update_or_create(
        speed_tier=1,
        is_active=True,
        defaults={
            "mini_unit_output_per_min": Decimal("15.0000"),
            "buildings_per_regular_belt": 4,
            "space_belt_full_belt_count": 48,
            "output_unit": "shapes_per_min",
            "source_kind": "EVTC_CANON",
            "source_note": (
                "Shapez 2 1.0 tier-1 Space Belt saturated cap factors "
                "(wiki sanity space_belt_max=2880). EVTC spec: " + EVTC_SPEC
            ),
        },
    )
    Fluid.objects.update_or_create(
        speed_tier=1,
        is_active=True,
        defaults={
            "fluid_launcher_output_per_min": Decimal("1200.0000"),
            "space_pipe_full_fluid_launcher_count": 288,
            "output_unit": "liters_per_min",
            "source_kind": "EVTC_CANON",
            "source_note": (
                "Shapez 2 1.0 tier-1 Space Pipe saturated cap factors "
                "(wiki sanity space_pipe_max=345600). EVTC spec: " + EVTC_SPEC
            ),
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0026_mining_extraction_rule"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExteriorShapeTransportCapacity",
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
                ("speed_tier", models.PositiveSmallIntegerField()),
                (
                    "mini_unit_output_per_min",
                    models.DecimalField(decimal_places=4, max_digits=12),
                ),
                ("buildings_per_regular_belt", models.PositiveSmallIntegerField()),
                ("space_belt_full_belt_count", models.PositiveSmallIntegerField()),
                ("output_unit", models.CharField(default="shapes_per_min", max_length=64)),
                (
                    "source_kind",
                    models.CharField(
                        choices=[("EVTC_CANON", "EVTC canonical")],
                        default="EVTC_CANON",
                        max_length=32,
                    ),
                ),
                ("source_note", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "exterior shape transport capacity",
                "verbose_name_plural": "⑧ EVTC · Shape transport capacity",
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("is_active", True)),
                        fields=("speed_tier",),
                        name="unique_active_exterior_shape_transport_per_tier",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="ExteriorFluidTransportCapacity",
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
                ("speed_tier", models.PositiveSmallIntegerField()),
                (
                    "fluid_launcher_output_per_min",
                    models.DecimalField(decimal_places=4, max_digits=12),
                ),
                ("space_pipe_full_fluid_launcher_count", models.PositiveSmallIntegerField()),
                ("output_unit", models.CharField(default="liters_per_min", max_length=64)),
                (
                    "source_kind",
                    models.CharField(
                        choices=[("EVTC_CANON", "EVTC canonical")],
                        default="EVTC_CANON",
                        max_length=32,
                    ),
                ),
                ("source_note", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "exterior fluid transport capacity",
                "verbose_name_plural": "⑧ EVTC · Fluid transport capacity",
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("is_active", True)),
                        fields=("speed_tier",),
                        name="unique_active_exterior_fluid_transport_per_tier",
                    )
                ],
            },
        ),
        migrations.RunPython(
            seed_exterior_transport_capacity_tier1,
            migrations.RunPython.noop,
        ),
    ]
