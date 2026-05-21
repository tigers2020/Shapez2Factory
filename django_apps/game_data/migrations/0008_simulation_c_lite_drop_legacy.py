# Drop Phase A legacy simulation tables and runtime_audit.simulation_entry FK.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0007_simulation_c_lite_validate"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="simulationruntimeaudit",
            name="simulation_entry",
        ),
        migrations.DeleteModel(
            name="SimulationFactoryStub",
        ),
        migrations.DeleteModel(
            name="SimulationSystemEntry",
        ),
        migrations.AlterField(
            model_name="simulationruntimeaudit",
            name="simulation_system",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="runtime_audit",
                to="game_data.simulationsystem",
                null=True,
                blank=True,
            ),
        ),
    ]
