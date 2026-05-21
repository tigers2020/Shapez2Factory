# ruff: noqa: E501

import re

import django.db.models.deletion
from django.apps import apps as django_apps
from django.db import migrations, models


def seed_taxonomy(apps, schema_editor):
    Namespace = apps.get_model("game_data", "GameDataNamespace")
    Section = apps.get_model("game_data", "GameDataSection")
    ns_order = 0
    seen_ns: dict[str, object] = {}
    section_re = re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪]+\s+([^·]+)\s*·\s*(.+)$")
    for model in django_apps.get_app_config("game_data").get_models():
        plural = str(model._meta.verbose_name_plural or "")
        match = section_re.match(plural)
        if not match:
            continue
        ns_label, sec_label = match.group(1).strip(), match.group(2).strip()
        ns_code = re.sub(r"[^a-z0-9]+", "_", ns_label.lower()).strip("_") or "misc"
        sec_code = re.sub(r"[^a-z0-9]+", "_", sec_label.lower()).strip("_") or "misc"
        if ns_code not in seen_ns:
            ns_order += 1
            seen_ns[ns_code] = Namespace.objects.create(
                code=ns_code,
                label=ns_label,
                order=ns_order,
            )
        namespace = seen_ns[ns_code]
        Section.objects.update_or_create(
            namespace=namespace,
            code=sec_code,
            defaults={
                "label": sec_label,
                "order": Section.objects.filter(namespace=namespace).count(),
                "django_model_label": f"game_data.{model.__name__}",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0015_toolbar_cross_refs"),
    ]

    operations = [
        migrations.CreateModel(
            name="GameDataNamespace",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("code", models.CharField(max_length=64, unique=True)),
                ("label", models.CharField(max_length=128)),
                ("order", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "game data namespace",
                "verbose_name_plural": "⑩ Taxonomy · Namespaces",
                "ordering": ["order", "code"],
            },
        ),
        migrations.CreateModel(
            name="GameDataSection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("code", models.CharField(max_length=128)),
                ("label", models.CharField(max_length=128)),
                ("order", models.PositiveIntegerField(default=0)),
                ("django_model_label", models.CharField(blank=True, default="", max_length=128)),
                (
                    "namespace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sections",
                        to="game_data.gamedatanamespace",
                    ),
                ),
            ],
            options={
                "verbose_name": "game data section",
                "verbose_name_plural": "⑩ Taxonomy · Sections",
                "ordering": ["namespace__order", "order", "code"],
            },
        ),
        migrations.AddConstraint(
            model_name="gamedatasection",
            constraint=models.UniqueConstraint(
                fields=("namespace", "code"),
                name="uq_gamedata_section_namespace_code",
            ),
        ),
        migrations.RunPython(seed_taxonomy, migrations.RunPython.noop),
    ]
