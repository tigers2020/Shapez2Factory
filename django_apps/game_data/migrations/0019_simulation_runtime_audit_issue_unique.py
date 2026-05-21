# ruff: noqa: E501

from django.db import migrations, models
from django.db.models import Count, Min


def dedupe_simulation_runtime_audit_issues(apps, schema_editor):
    Issue = apps.get_model("game_data", "SimulationRuntimeAuditIssue")
    dup_groups = (
        Issue.objects.values("simulation_system_id", "issue_code")
        .annotate(keep_id=Min("id"), cnt=Count("id"))
        .filter(cnt__gt=1)
    )
    for group in dup_groups:
        Issue.objects.filter(
            simulation_system_id=group["simulation_system_id"],
            issue_code=group["issue_code"],
        ).exclude(pk=group["keep_id"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0018_simulation_audit_issues"),
    ]

    operations = [
        migrations.RunPython(dedupe_simulation_runtime_audit_issues, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="simulationruntimeauditissue",
            constraint=models.UniqueConstraint(
                fields=("simulation_system", "issue_code"),
                name="uq_sim_runtime_audit_issue_system_code",
            ),
        ),
    ]
