# Validate C-lite schema integrity before dropping legacy tables.

from django.db import migrations


def validate_simulation_schema(apps, schema_editor):
    SimulationProfile = apps.get_model("game_data", "SimulationProfile")
    if SimulationProfile.objects.count() < 1:
        raise RuntimeError("SimulationProfile seeds missing — run 0005 seed")


def validate_before_legacy_drop(apps, schema_editor):
    legacy_count = apps.get_model("game_data", "SimulationSystemEntry").objects.count()
    if legacy_count > 0:
        raise RuntimeError(
            "SimulationSystemEntry rows remain — run 0006 clear or re-apply migrations"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0006_simulation_c_lite_data"),
    ]

    operations = [
        migrations.RunPython(validate_simulation_schema, migrations.RunPython.noop),
        migrations.RunPython(validate_before_legacy_drop, migrations.RunPython.noop),
    ]
