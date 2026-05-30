# Generated manually to restore local-only migration name recorded in django_migrations.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("asteroid_lab", "0013_reconstructed_map_admin_thumbnail"),
    ]

    operations = [
        migrations.AddField(
            model_name="solverrun",
            name="lab_replay_manifest_summary_json",
            field=models.JSONField(
                default=dict,
                help_text="UI cache mirror of lab replay manifest summary (not solver input).",
            ),
        ),
        migrations.AddField(
            model_name="solverrun",
            name="lab_replay_payload_json",
            field=models.JSONField(
                default=dict,
                help_text="UI cache mirror of composed lab replay payload (not solver input).",
            ),
        ),
        migrations.AddField(
            model_name="solverrun",
            name="solver_summary_json",
            field=models.JSONField(
                default=dict,
                help_text="UI cache mirror of solver_summary (not solver input).",
            ),
        ),
    ]
