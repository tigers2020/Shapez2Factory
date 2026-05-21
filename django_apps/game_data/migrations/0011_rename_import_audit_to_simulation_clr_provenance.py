# Rename ImportAudit → SimulationClrProvenance (CLR provenance, not import audit log).

from django.db import migrations, models


def _rewrite_clr_provenance_canonical_ids(apps, schema_editor) -> None:
    Model = apps.get_model("game_data", "SimulationClrProvenance")
    for row in Model.objects.filter(canonical_id__startswith="import-audit:"):
        row.canonical_id = row.canonical_id.replace("import-audit:", "sim-clr-prov:", 1)
        row.save(update_fields=["canonical_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0010_unknown_property_reason_code"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="ImportAudit",
            new_name="SimulationClrProvenance",
        ),
        migrations.AlterModelOptions(
            name="simulationclrprovenance",
            options={
                "verbose_name": "simulation CLR provenance",
                "verbose_name_plural": "⑥ Simulation · CLR provenance",
            },
        ),
        migrations.AlterField(
            model_name="simulationclrprovenance",
            name="import_batch",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="simulation_clr_provenances",
                to="game_data.importbatch",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="simulationclrprovenance",
            name="uq_import_audit_batch_stable_file",
        ),
        migrations.AddConstraint(
            model_name="simulationclrprovenance",
            constraint=models.UniqueConstraint(
                fields=("import_batch", "source_stable_id", "source_file"),
                name="uq_sim_clr_prov_batch_stable_file",
            ),
        ),
        migrations.RunPython(_rewrite_clr_provenance_canonical_ids, migrations.RunPython.noop),
    ]
