"""Rename GeneticSample -> GeneSeed (gene = DB seed rows only)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("asteroid_lab", "0017_solverrun_artifact_root_lifecycle_status"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="GeneticSample",
            new_name="GeneSeed",
        ),
        migrations.RemoveConstraint(
            model_name="geneseed",
            name="uniq_genetic_sample_gene_key_when_set",
        ),
        migrations.AddConstraint(
            model_name="geneseed",
            constraint=models.UniqueConstraint(
                fields=("gene_key",),
                name="uniq_gene_seed_gene_key_when_set",
                condition=models.Q(gene_key__isnull=False),
            ),
        ),
        migrations.AlterModelOptions(
            name="geneseed",
            options={
                "ordering": ("-updated_at",),
                "verbose_name": "Gene seed",
                "verbose_name_plural": "Gene seeds",
            },
        ),
    ]
