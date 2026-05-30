# Generated manually to restore local-only migration name recorded in django_migrations.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("asteroid_lab", "0015_backfill_solverrun_fast_cache_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="solverrun",
            name="solver_runtime_replay_frames_json",
            field=models.JSONField(
                default=list,
                help_text="UI cache mirror of solver_runtime_replay_frames (not solver input).",
            ),
        ),
    ]
