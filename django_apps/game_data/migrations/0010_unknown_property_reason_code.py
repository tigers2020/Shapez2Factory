# UnknownProperty: reason_code + classification; UK for idempotent simulation ignores.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0009_simulation_parameter_registry"),
    ]

    operations = [
        migrations.AddField(
            model_name="unknownproperty",
            name="reason_code",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="unknownproperty",
            name="classification",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddIndex(
            model_name="unknownproperty",
            index=models.Index(
                fields=["import_batch", "reason_code"],
                name="gd_unknownprop_batch_reason",
            ),
        ),
        migrations.AddConstraint(
            model_name="unknownproperty",
            constraint=models.UniqueConstraint(
                fields=("import_batch", "owner_model", "owner_key", "json_path"),
                name="uq_unknown_property_batch_owner_path",
            ),
        ),
    ]
