# Typed per-system speed tables: SimulationBuffableSpeed, SimulationMultipleBeltSpeed.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0011_rename_import_audit_to_simulation_clr_provenance"),
    ]

    operations = [
        migrations.CreateModel(
            name="SimulationBuffableSpeed",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("canonical_id", models.CharField(max_length=255, unique=True)),
                ("parameter_name", models.CharField(max_length=100)),
                ("dump_type", models.CharField(default="BuffableBeltSpeed", max_length=64)),
                ("base_speed", models.CharField(blank=True, default="", max_length=64)),
                ("steps_per_tick", models.PositiveIntegerField(default=0)),
                (
                    "research_upgrade",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="buffable_speeds",
                        to="game_data.researchupgrade",
                    ),
                ),
                (
                    "simulation_system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="buffable_speeds",
                        to="game_data.simulationsystem",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation buffable speed",
                "verbose_name_plural": "⑥ Simulation · Buffable speeds",
            },
        ),
        migrations.CreateModel(
            name="SimulationMultipleBeltSpeed",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("canonical_id", models.CharField(max_length=255, unique=True)),
                ("parameter_name", models.CharField(default="JumpSpeed", max_length=100)),
                ("dump_type", models.CharField(default="MultipleBeltSpeed", max_length=64)),
                ("multiplier", models.PositiveIntegerField(default=0)),
                ("steps_per_tick", models.PositiveIntegerField(default=0)),
                (
                    "buffable_base",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="multiple_speed_children",
                        to="game_data.simulationbuffablespeed",
                    ),
                ),
                (
                    "simulation_system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="multiple_belt_speeds",
                        to="game_data.simulationsystem",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation multiple belt speed",
                "verbose_name_plural": "⑥ Simulation · Multiple belt speeds",
            },
        ),
        migrations.AddConstraint(
            model_name="simulationbuffablespeed",
            constraint=models.UniqueConstraint(
                fields=("simulation_system", "parameter_name"),
                name="uq_sim_buffable_speed_system_param",
            ),
        ),
        migrations.AddConstraint(
            model_name="simulationmultiplebeltspeed",
            constraint=models.UniqueConstraint(
                fields=("simulation_system", "parameter_name"),
                name="uq_sim_multiple_belt_speed_system_param",
            ),
        ),
    ]
