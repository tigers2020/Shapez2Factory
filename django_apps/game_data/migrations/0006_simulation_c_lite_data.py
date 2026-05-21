# Clear legacy simulation rows — C-lite data comes from the next import_game_data run.

from django.db import migrations


def clear_legacy_simulation_rows(apps, schema_editor):
    for model_name in (
        "SimulationFactoryStub",
        "SimulationRuntimeAudit",
        "SimulationSystemEntry",
    ):
        apps.get_model("game_data", model_name).objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0005_simulation_c_lite_create"),
    ]

    operations = [
        migrations.RunPython(clear_legacy_simulation_rows, migrations.RunPython.noop),
    ]
