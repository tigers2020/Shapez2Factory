# Simulation parameter key registry + per-system occurrences (no values).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0008_simulation_c_lite_drop_legacy"),
    ]

    operations = [
        migrations.CreateModel(
            name="SimulationSystemParameterKey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, unique=True)),
                (
                    "classification",
                    models.CharField(
                        choices=[
                            ("domain_config", "Domain config"),
                            ("runtime_state", "Runtime state"),
                            ("event_delegate", "Event delegate"),
                            ("reflection_dump", "Reflection dump"),
                            ("cache_snapshot", "Cache snapshot"),
                            ("ignored_runtime", "Ignored runtime"),
                            ("unknown", "Unknown"),
                        ],
                        default="unknown",
                        max_length=50,
                    ),
                ),
                ("occurrence_count", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "simulation parameter key",
                "verbose_name_plural": "⑥ Simulation · Parameter keys",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="SimulationSystemParameterOccurrence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_path", models.CharField(max_length=1000)),
                (
                    "parameter_key",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="occurrences",
                        to="game_data.simulationsystemparameterkey",
                    ),
                ),
                (
                    "simulation_system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parameter_occurrences",
                        to="game_data.simulationsystem",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation parameter occurrence",
                "verbose_name_plural": "⑥ Simulation · Parameter occurrences",
            },
        ),
        migrations.AddConstraint(
            model_name="simulationsystemparameteroccurrence",
            constraint=models.UniqueConstraint(
                fields=("simulation_system", "parameter_key"),
                name="uq_sim_param_occurrence_system_key",
            ),
        ),
    ]
