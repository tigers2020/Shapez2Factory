# C-lite simulation schema — create new tables only (legacy tables unchanged).
# ruff: noqa: E501

import django.db.models.deletion
from django.db import migrations, models

_PROFILE_SEEDS = (
    ("factory", "Simulation factory stub"),
    ("connectable_graph", "Connectable simulation graph"),
    ("converter_runtime", "Converter runtime capture"),
    ("belt_policy", "Global belt speed policy"),
    ("other", "Other simulation parameters"),
)


def seed_simulation_profiles(apps, schema_editor):
    SimulationProfile = apps.get_model("game_data", "SimulationProfile")
    for key, name in _PROFILE_SEEDS:
        SimulationProfile.objects.get_or_create(profile_key=key, defaults={"profile_name": name})


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0004_toolbar_tree_node_hierarchy"),
    ]

    operations = [
        migrations.CreateModel(
            name="SimulationProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("profile_key", models.CharField(max_length=64, unique=True)),
                ("profile_name", models.CharField(blank=True, default="", max_length=128)),
            ],
            options={
                "verbose_name": "simulation profile",
                "verbose_name_plural": "⑥ Simulation · Profiles",
            },
        ),
        migrations.CreateModel(
            name="SimulationSystem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("source_stable_id", models.CharField(max_length=64)),
                ("source_row_index", models.PositiveIntegerField()),
                ("system_family", models.CharField(max_length=128)),
                ("canonical_id", models.CharField(db_index=True, max_length=255)),
                ("display_name_key", models.CharField(blank=True, default="", max_length=512)),
                (
                    "import_batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="simulation_systems",
                        to="game_data.importbatch",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="systems",
                        to="game_data.simulationprofile",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation system",
                "verbose_name_plural": "⑥ Simulation · Systems",
            },
        ),
        migrations.AddConstraint(
            model_name="simulationsystem",
            constraint=models.UniqueConstraint(
                fields=("import_batch", "source_stable_id"),
                name="uq_simulation_system_batch_stable",
            ),
        ),
        migrations.CreateModel(
            name="SimulationType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("simulation_class", models.CharField(max_length=128)),
                ("assembly_name", models.CharField(blank=True, default="", max_length=128)),
                (
                    "simulation_system",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="simulation_type",
                        to="game_data.simulationsystem",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation type",
                "verbose_name_plural": "⑥ Simulation · Types",
            },
        ),
        migrations.CreateModel(
            name="SimulationStateType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("state_class", models.CharField(max_length=128)),
                ("assembly_name", models.CharField(blank=True, default="", max_length=128)),
                (
                    "simulation_system",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="state_type",
                        to="game_data.simulationsystem",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation state type",
                "verbose_name_plural": "⑥ Simulation · State types",
            },
        ),
        migrations.CreateModel(
            name="ImportAudit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("canonical_id", models.CharField(max_length=255, unique=True)),
                (
                    "source_file",
                    models.CharField(default="simulation_systems.json", max_length=128),
                ),
                ("source_stable_id", models.CharField(max_length=64)),
                ("source_row_index", models.PositiveIntegerField()),
                ("clr_type_string", models.TextField()),
                ("profile_signature", models.CharField(blank=True, default="", max_length=128)),
                (
                    "import_batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="import_audits",
                        to="game_data.importbatch",
                    ),
                ),
            ],
            options={
                "verbose_name": "import audit",
                "verbose_name_plural": "⑥ Simulation · Import audit",
            },
        ),
        migrations.AddConstraint(
            model_name="importaudit",
            constraint=models.UniqueConstraint(
                fields=("import_batch", "source_stable_id", "source_file"),
                name="uq_import_audit_batch_stable_file",
            ),
        ),
        migrations.CreateModel(
            name="ConnectableSimulation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("canonical_id", models.CharField(max_length=255, unique=True)),
                ("connectable_key", models.CharField(max_length=64)),
                ("attachment_index", models.PositiveIntegerField()),
                ("num_connectors", models.PositiveIntegerField(default=0)),
                ("num_occupied_tiles", models.PositiveIntegerField(default=0)),
                ("connector_signature", models.CharField(blank=True, default="", max_length=512)),
                ("lane_signature", models.CharField(blank=True, default="", max_length=512)),
                (
                    "building_variant",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="connectables",
                        to="game_data.buildingvariant",
                    ),
                ),
                (
                    "simulation_system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="connectables",
                        to="game_data.simulationsystem",
                    ),
                ),
            ],
            options={
                "verbose_name": "connectable simulation",
                "verbose_name_plural": "⑥ Simulation · Connectables",
            },
        ),
        migrations.AddConstraint(
            model_name="connectablesimulation",
            constraint=models.UniqueConstraint(
                fields=("simulation_system", "connectable_key"),
                name="uq_connectable_system_key",
            ),
        ),
        migrations.CreateModel(
            name="SimulationConnector",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("canonical_id", models.CharField(max_length=255, unique=True)),
                ("order_index", models.PositiveIntegerField()),
                ("direction", models.CharField(blank=True, default="", max_length=32)),
                ("connector_role", models.CharField(blank=True, default="", max_length=64)),
                ("io_channel_type", models.CharField(blank=True, default="", max_length=32)),
                (
                    "connectable_simulation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="connectors",
                        to="game_data.connectablesimulation",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation connector",
                "verbose_name_plural": "⑥ Simulation · Connectors",
                "ordering": ["order_index"],
            },
        ),
        migrations.AddConstraint(
            model_name="simulationconnector",
            constraint=models.UniqueConstraint(
                fields=("connectable_simulation", "order_index"),
                name="uq_sim_connector_order",
            ),
        ),
        migrations.CreateModel(
            name="SimulationConnectorProperty",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("property_key", models.CharField(max_length=64)),
                ("value_int", models.BigIntegerField(blank=True, null=True)),
                ("value_float", models.FloatField(blank=True, null=True)),
                ("value_bool", models.BooleanField(blank=True, null=True)),
                ("value_text", models.TextField(blank=True, default="")),
                (
                    "connector",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="properties",
                        to="game_data.simulationconnector",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation connector property",
                "verbose_name_plural": "⑥ Simulation · Connector properties",
            },
        ),
        migrations.AddConstraint(
            model_name="simulationconnectorproperty",
            constraint=models.UniqueConstraint(
                fields=("connector", "property_key"),
                name="uq_sim_connector_property_key",
            ),
        ),
        migrations.CreateModel(
            name="SimulationLaneDefinition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("canonical_id", models.CharField(max_length=255, unique=True)),
                ("lane_key", models.CharField(max_length=64)),
                ("lane_index", models.PositiveIntegerField()),
                ("capacity", models.PositiveIntegerField(blank=True, null=True)),
                ("direction", models.CharField(blank=True, default="", max_length=32)),
                ("transport_type", models.CharField(blank=True, default="", max_length=64)),
                (
                    "connectable_simulation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lane_definitions",
                        to="game_data.connectablesimulation",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation lane definition",
                "verbose_name_plural": "⑥ Simulation · Lane definitions",
                "ordering": ["lane_index"],
            },
        ),
        migrations.AddConstraint(
            model_name="simulationlanedefinition",
            constraint=models.UniqueConstraint(
                fields=("connectable_simulation", "lane_key"),
                name="uq_lane_definition_key",
            ),
        ),
        migrations.CreateModel(
            name="SimulationLaneRuntimeState",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("state_key", models.CharField(max_length=64)),
                ("state_value_text", models.TextField(blank=True, default="")),
                (
                    "lane_definition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="runtime_states",
                        to="game_data.simulationlanedefinition",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation lane runtime state",
                "verbose_name_plural": "⑥ Simulation · Lane runtime states",
            },
        ),
        migrations.AddConstraint(
            model_name="simulationlaneruntimestate",
            constraint=models.UniqueConstraint(
                fields=("lane_definition", "state_key"),
                name="uq_lane_runtime_state_key",
            ),
        ),
        migrations.CreateModel(
            name="SimulationChunkBounds",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("order_index", models.PositiveSmallIntegerField(default=0)),
                ("min_x", models.IntegerField(default=0)),
                ("min_y", models.IntegerField(default=0)),
                ("min_z", models.IntegerField(default=0)),
                ("max_x", models.IntegerField(default=0)),
                ("max_y", models.IntegerField(default=0)),
                ("max_z", models.IntegerField(default=0)),
                (
                    "connectable_simulation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chunk_bounds",
                        to="game_data.connectablesimulation",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation chunk bounds",
                "verbose_name_plural": "⑥ Simulation · Chunk bounds",
            },
        ),
        migrations.CreateModel(
            name="SimulationTileBounds",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("order_index", models.PositiveSmallIntegerField(default=0)),
                ("min_x", models.IntegerField(default=0)),
                ("min_y", models.IntegerField(default=0)),
                ("min_z", models.IntegerField(default=0)),
                ("max_x", models.IntegerField(default=0)),
                ("max_y", models.IntegerField(default=0)),
                ("max_z", models.IntegerField(default=0)),
                (
                    "connectable_simulation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tile_bounds",
                        to="game_data.connectablesimulation",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation tile bounds",
                "verbose_name_plural": "⑥ Simulation · Tile bounds",
            },
        ),
        migrations.AddField(
            model_name="globalbeltspeedpolicy",
            name="simulation_system",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="belt_speed_policy",
                to="game_data.simulationsystem",
            ),
        ),
        migrations.AlterField(
            model_name="simulationruntimeaudit",
            name="simulation_entry",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="runtime_audit",
                to="game_data.simulationsystementry",
            ),
        ),
        migrations.AddField(
            model_name="simulationruntimeaudit",
            name="simulation_system",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="runtime_audit_system",
                to="game_data.simulationsystem",
            ),
        ),
        migrations.RunPython(seed_simulation_profiles, migrations.RunPython.noop),
    ]
