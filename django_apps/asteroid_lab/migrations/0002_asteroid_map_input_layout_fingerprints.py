"""Add layout fingerprint columns to AsteroidMapInput."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("asteroid_lab", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="asteroidmapinput",
            name="layout_fingerprint",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AddField(
            model_name="asteroidmapinput",
            name="absolute_layout_fingerprint",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
    ]
