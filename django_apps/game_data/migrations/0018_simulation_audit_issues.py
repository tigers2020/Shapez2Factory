# ruff: noqa: E501

import django.db.models.deletion
from django.db import migrations, models


def migrate_audit_blobs(apps, schema_editor):
    Audit = apps.get_model("game_data", "SimulationRuntimeAudit")
    Issue = apps.get_model("game_data", "SimulationRuntimeAuditIssue")
    for audit in Audit.objects.select_related("simulation_system").iterator():
        if not audit.simulation_system_id:
            continue
        blob = audit.audit_blob or {}
        if not blob:
            continue
        Issue.objects.update_or_create(
            simulation_system_id=audit.simulation_system_id,
            issue_code="converter_profile",
            defaults={
                "severity": "info",
                "message": str(blob)[:2000],
                "source_path": f"legacy_audit:{audit.pk}",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0017_game_data_reference"),
    ]

    operations = [
        migrations.CreateModel(
            name="SimulationRuntimeAuditIssue",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "issue_code",
                    models.CharField(
                        choices=[
                            ("converter_profile", "Converter profile capture"),
                            ("runtime_stub", "Runtime stub"),
                            ("unknown", "Unknown"),
                        ],
                        default="unknown",
                        max_length=128,
                    ),
                ),
                (
                    "severity",
                    models.CharField(
                        choices=[("info", "Info"), ("warning", "Warning"), ("error", "Error")],
                        default="info",
                        max_length=32,
                    ),
                ),
                ("message", models.TextField()),
                ("source_path", models.CharField(blank=True, default="", max_length=512)),
                (
                    "simulation_system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="audit_issues",
                        to="game_data.simulationsystem",
                    ),
                ),
            ],
            options={
                "verbose_name": "simulation runtime audit issue",
                "verbose_name_plural": "⑥ Simulation · Runtime audit issues",
                "ordering": ["simulation_system_id", "issue_code"],
            },
        ),
        migrations.RunPython(migrate_audit_blobs, migrations.RunPython.noop),
        migrations.DeleteModel(
            name="SimulationRuntimeAudit",
        ),
    ]
