# Generated manually for island extractor reference blueprints.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("asteroid_lab", "0010_solverrun_status_partial"),
    ]

    operations = [
        migrations.CreateModel(
            name="IslandExtractorBlueprint",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "variant_key",
                    models.CharField(
                        help_text="예: shape_balance, shape_omni, fluid_default",
                        max_length=64,
                        unique=True,
                        verbose_name="variant key",
                    ),
                ),
                ("carrier_kind", models.CharField(max_length=16, verbose_name="carrier")),
                ("display_name", models.CharField(max_length=120, verbose_name="표시 이름")),
                ("summary", models.TextField(blank=True, verbose_name="설명")),
                ("layout_t", models.CharField(max_length=80, verbose_name="Layout T")),
                ("copy_code", models.TextField(verbose_name="SHAPEZ2-4- 복사 문자열")),
                (
                    "inner_fingerprint",
                    models.CharField(
                        blank=True,
                        max_length=64,
                        verbose_name="내부 B.Entries 지문",
                    ),
                ),
                (
                    "metadata_json",
                    models.JSONField(blank=True, default=dict, verbose_name="메타데이터"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "섬 추출기 기본 블루프린트",
                "verbose_name_plural": "섬 추출기 기본 블루프린트",
                "ordering": ("variant_key",),
                "indexes": [
                    models.Index(
                        fields=["carrier_kind", "variant_key"],
                        name="asteroid_la_carrier_0c8f2a_idx",
                    )
                ],
            },
        ),
    ]
