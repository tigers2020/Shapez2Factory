# Generated manually for map overwrite / updated_at tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("asteroid_lab", "0006_reconstructed_map_layers"),
    ]

    operations = [
        migrations.AddField(
            model_name="asteroidmapinput",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="reconstructedasteroidmap",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterModelOptions(
            name="reconstructedasteroidmap",
            options={
                "ordering": ("-updated_at",),
                "verbose_name": "복원 소행성 맵",
                "verbose_name_plural": "복원 소행성 맵",
            },
        ),
        migrations.AddIndex(
            model_name="asteroidmapinput",
            index=models.Index(fields=["-updated_at"], name="asteroid_la_mapinp_upd_idx"),
        ),
        migrations.AddIndex(
            model_name="reconstructedasteroidmap",
            index=models.Index(fields=["-updated_at"], name="asteroid_la_recon_upd_idx"),
        ),
    ]
