# Generated manually for IVVD lookup normalization (category + global enums + issue codes).

import django.db.models.deletion
from django.db import migrations, models


def _seed_lookups(apps, schema_editor) -> None:  # noqa: ARG001
    Sever = apps.get_model("shapez_core", "ShapezIvvdSeverity")
    for code, label, so in (
        ("error", "Error", 0),
        ("warning", "Warning", 1),
    ):
        Sever.objects.update_or_create(code=code, defaults={"label": label, "sort_order": so})

    Phase = apps.get_model("shapez_core", "ShapezIvvdValidationPhase")
    for so, code in enumerate(("schema", "xref", "semantic")):
        Phase.objects.update_or_create(code=code, defaults={"label": code, "sort_order": so})

    Life = apps.get_model("shapez_core", "ShapezIvvdLifecycleStatus")
    for so, (code, label) in enumerate(
        (
            ("imported", "Imported"),
            ("schema_checked", "Schema checked"),
            ("xref_checked", "Cross-ref checked"),
            ("semantic_checked", "Semantic checked"),
            ("sealed", "Sealed"),
            ("failed", "Failed"),
        )
    ):
        Life.objects.update_or_create(code=code, defaults={"label": label, "sort_order": so})

    DK = apps.get_model("shapez_core", "ShapezIvvdDocumentKind")
    kinds = (
        ("identifiers", "identifiers.json"),
        ("buildings", "buildings.json"),
        ("translations", "translations"),
        ("scenario", "scenario"),
        ("difficulty_preset", "difficulty preset"),
        ("scenario_parameter_preset", "scenario parameter preset"),
        ("json_schema", "json schema"),
        ("version", "version file"),
        ("other", "other"),
    )
    for so, (code, label) in enumerate(kinds):
        DK.objects.update_or_create(code=code, defaults={"label": label, "sort_order": so})

    AT = apps.get_model("shapez_core", "ShapezIvvdArtifactType")
    AT.objects.update_or_create(
        code="ivvd_import_bundle",
        defaults={"label": "IVVD import bundle", "sort_order": 0},
    )


def _port_release_integrity(apps, schema_editor) -> None:  # noqa: ARG001
    Release = apps.get_model("shapez_core", "ShapezBasedataRelease")
    for r in Release.objects.all():
        r.integrity_status_new_id = r.integrity_status
        r.save(update_fields=["integrity_status_new_id"])


def _port_document_kind(apps, schema_editor) -> None:  # noqa: ARG001
    Doc = apps.get_model("shapez_core", "ShapezBasedataDocument")
    for d in Doc.objects.all():
        d.document_kind_new_id = d.kind
        d.save(update_fields=["document_kind_new_id"])


def _port_validation_phase(apps, schema_editor) -> None:  # noqa: ARG001
    Run = apps.get_model("shapez_core", "ShapezValidationRun")
    for run in Run.objects.all():
        run.validation_phase_new_id = run.validation_phase
        run.save(update_fields=["validation_phase_new_id"])


def _port_integrity_issues(apps, schema_editor) -> None:  # noqa: ARG001
    Issue = apps.get_model("shapez_core", "ShapezIntegrityIssue")
    IssueCode = apps.get_model("shapez_core", "ShapezIntegrityIssueCode")
    Sever = apps.get_model("shapez_core", "ShapezIvvdSeverity")
    for issue in Issue.objects.all():
        sev = Sever.objects.get(code=issue.severity)
        ic, _ = IssueCode.objects.get_or_create(
            code=issue.issue_code,
            defaults={"summary": "", "default_severity": sev},
        )
        issue.severity_new_id = sev.code
        issue.issue_type_new_id = ic.code
        issue.save(update_fields=["severity_new_id", "issue_type_new_id"])


def _port_artifact_type(apps, schema_editor) -> None:  # noqa: ARG001
    Art = apps.get_model("shapez_core", "ShapezCanonicalArtifact")
    for a in Art.objects.all():
        a.artifact_type_new_id = a.artifact_type
        a.save(update_fields=["artifact_type_new_id"])


def _port_identifier_categories(apps, schema_editor) -> None:  # noqa: ARG001
    Cat = apps.get_model("shapez_core", "ShapezIdentifierCategory")
    Gid = apps.get_model("shapez_core", "ShapezGameIdentifier")
    for row in Gid.objects.all():
        cat, _ = Cat.objects.get_or_create(
            release_id=row.release_id,
            key=row.category,
            defaults={"sort_order": 0, "label": ""},
        )
        row.identifier_category_tmp_id = cat.pk
        row.save(update_fields=["identifier_category_tmp_id"])


def _noop_reverse(apps, schema_editor) -> None:  # noqa: ARG001
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("shapez_core", "0001_initial_ivvd"),
    ]

    operations = [
        migrations.CreateModel(
            name="ShapezIvvdSeverity",
            fields=[
                ("code", models.SlugField(max_length=32, primary_key=True, serialize=False)),
                ("label", models.CharField(max_length=80)),
                ("sort_order", models.SmallIntegerField(default=0)),
            ],
            options={
                "ordering": ("sort_order", "code"),
                "verbose_name_plural": "IVVD severities",
            },
        ),
        migrations.CreateModel(
            name="ShapezIvvdValidationPhase",
            fields=[
                ("code", models.SlugField(max_length=40, primary_key=True, serialize=False)),
                ("label", models.CharField(blank=True, max_length=80)),
                ("sort_order", models.SmallIntegerField(default=0)),
            ],
            options={
                "ordering": ("sort_order", "code"),
                "verbose_name_plural": "IVVD validation phases",
            },
        ),
        migrations.CreateModel(
            name="ShapezIvvdLifecycleStatus",
            fields=[
                ("code", models.SlugField(max_length=40, primary_key=True, serialize=False)),
                ("label", models.CharField(blank=True, max_length=80)),
                ("sort_order", models.SmallIntegerField(default=0)),
            ],
            options={
                "ordering": ("sort_order", "code"),
                "verbose_name_plural": "IVVD lifecycle statuses",
            },
        ),
        migrations.CreateModel(
            name="ShapezIvvdDocumentKind",
            fields=[
                ("code", models.SlugField(max_length=40, primary_key=True, serialize=False)),
                ("label", models.CharField(blank=True, max_length=120)),
                ("sort_order", models.SmallIntegerField(default=0)),
            ],
            options={
                "ordering": ("sort_order", "code"),
                "verbose_name_plural": "IVVD document kinds",
            },
        ),
        migrations.CreateModel(
            name="ShapezIvvdArtifactType",
            fields=[
                ("code", models.SlugField(max_length=80, primary_key=True, serialize=False)),
                ("label", models.CharField(blank=True, max_length=120)),
                ("sort_order", models.SmallIntegerField(default=0)),
            ],
            options={
                "ordering": ("sort_order", "code"),
                "verbose_name_plural": "IVVD artifact types",
            },
        ),
        migrations.CreateModel(
            name="ShapezIntegrityIssueCode",
            fields=[
                ("code", models.SlugField(max_length=80, primary_key=True, serialize=False)),
                ("summary", models.CharField(blank=True, max_length=240)),
                (
                    "default_severity",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="issue_codes_defaulting_here",
                        to="shapez_core.shapezivvdseverity",
                    ),
                ),
            ],
            options={
                "ordering": ("code",),
                "verbose_name_plural": "IVVD integrity issue codes",
            },
        ),
        migrations.RunPython(_seed_lookups, _noop_reverse),
        migrations.CreateModel(
            name="ShapezIdentifierCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("key", models.CharField(db_index=True, max_length=120)),
                ("sort_order", models.SmallIntegerField(default=0)),
                ("label", models.CharField(blank=True, max_length=160)),
                (
                    "release",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="identifier_categories",
                        to="shapez_core.shapezbasedatarelease",
                    ),
                ),
            ],
            options={
                "ordering": ("release", "sort_order", "key"),
            },
        ),
        migrations.AddConstraint(
            model_name="shapezidentifiercategory",
            constraint=models.UniqueConstraint(
                fields=("release", "key"),
                name="shapez_identifier_category_release_key_uniq",
            ),
        ),
        migrations.AddField(
            model_name="shapezbasedatarelease",
            name="integrity_status_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="releases_tmp",
                to="shapez_core.shapezivvdlifecyclestatus",
            ),
        ),
        migrations.RunPython(_port_release_integrity, _noop_reverse),
        migrations.RemoveField(
            model_name="shapezbasedatarelease",
            name="integrity_status",
        ),
        migrations.RenameField(
            model_name="shapezbasedatarelease",
            old_name="integrity_status_new",
            new_name="integrity_status",
        ),
        migrations.AlterField(
            model_name="shapezbasedatarelease",
            name="integrity_status",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="releases",
                to="shapez_core.shapezivvdlifecyclestatus",
            ),
        ),
        migrations.AddField(
            model_name="shapezbasedatadocument",
            name="document_kind_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="documents_tmp",
                to="shapez_core.shapezivvddocumentkind",
            ),
        ),
        migrations.RunPython(_port_document_kind, _noop_reverse),
        migrations.RemoveConstraint(
            model_name="shapezbasedatadocument",
            name="shapez_basedata_document_release_kind_logical_key_uniq",
        ),
        migrations.RemoveIndex(
            model_name="shapezbasedatadocument",
            name="shapez_core_release_91bb6e_idx",
        ),
        migrations.RemoveField(
            model_name="shapezbasedatadocument",
            name="kind",
        ),
        migrations.RenameField(
            model_name="shapezbasedatadocument",
            old_name="document_kind_new",
            new_name="document_kind",
        ),
        migrations.AlterField(
            model_name="shapezbasedatadocument",
            name="document_kind",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="documents",
                to="shapez_core.shapezivvddocumentkind",
                db_index=True,
            ),
        ),
        migrations.AddConstraint(
            model_name="shapezbasedatadocument",
            constraint=models.UniqueConstraint(
                fields=("release", "document_kind", "logical_key"),
                name="shapez_basedata_document_release_kind_logical_key_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="shapezbasedatadocument",
            index=models.Index(
                fields=["release", "document_kind"],
                name="shapez_core_doc_release_kind_idx",
            ),
        ),
        migrations.AddField(
            model_name="shapezvalidationrun",
            name="validation_phase_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="validation_runs_tmp",
                to="shapez_core.shapezivvdvalidationphase",
            ),
        ),
        migrations.RunPython(_port_validation_phase, _noop_reverse),
        migrations.RemoveIndex(
            model_name="shapezvalidationrun",
            name="shapez_core_release_487bf7_idx",
        ),
        migrations.RemoveField(
            model_name="shapezvalidationrun",
            name="validation_phase",
        ),
        migrations.RenameField(
            model_name="shapezvalidationrun",
            old_name="validation_phase_new",
            new_name="validation_phase",
        ),
        migrations.AlterField(
            model_name="shapezvalidationrun",
            name="validation_phase",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="validation_runs",
                to="shapez_core.shapezivvdvalidationphase",
                db_index=True,
            ),
        ),
        migrations.AddIndex(
            model_name="shapezvalidationrun",
            index=models.Index(
                fields=["release", "validation_phase", "-created_at"],
                name="shapez_core_release_487bf7_idx",
            ),
        ),
        migrations.AddField(
            model_name="shapezintegrityissue",
            name="severity_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="integrity_issues_tmp_sev",
                to="shapez_core.shapezivvdseverity",
            ),
        ),
        migrations.AddField(
            model_name="shapezintegrityissue",
            name="issue_type_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="integrity_issues_tmp_type",
                to="shapez_core.shapezintegrityissuecode",
            ),
        ),
        migrations.RunPython(_port_integrity_issues, _noop_reverse),
        migrations.RemoveIndex(
            model_name="shapezintegrityissue",
            name="shapez_core_release_001925_idx",
        ),
        migrations.RemoveField(
            model_name="shapezintegrityissue",
            name="severity",
        ),
        migrations.RemoveField(
            model_name="shapezintegrityissue",
            name="issue_code",
        ),
        migrations.RenameField(
            model_name="shapezintegrityissue",
            old_name="severity_new",
            new_name="severity",
        ),
        migrations.RenameField(
            model_name="shapezintegrityissue",
            old_name="issue_type_new",
            new_name="issue_type",
        ),
        migrations.AlterField(
            model_name="shapezintegrityissue",
            name="severity",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="integrity_issues",
                to="shapez_core.shapezivvdseverity",
            ),
        ),
        migrations.AlterField(
            model_name="shapezintegrityissue",
            name="issue_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="integrity_issues",
                to="shapez_core.shapezintegrityissuecode",
                db_index=True,
            ),
        ),
        migrations.AddIndex(
            model_name="shapezintegrityissue",
            index=models.Index(
                fields=["release", "issue_type"],
                name="shapez_core_issue_release_type_idx",
            ),
        ),
        migrations.AddField(
            model_name="shapezcanonicalartifact",
            name="artifact_type_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="artifacts_tmp",
                to="shapez_core.shapezivvdartifacttype",
            ),
        ),
        migrations.RunPython(_port_artifact_type, _noop_reverse),
        migrations.RemoveField(
            model_name="shapezcanonicalartifact",
            name="artifact_type",
        ),
        migrations.RenameField(
            model_name="shapezcanonicalartifact",
            old_name="artifact_type_new",
            new_name="artifact_type",
        ),
        migrations.AlterField(
            model_name="shapezcanonicalartifact",
            name="artifact_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="artifacts",
                to="shapez_core.shapezivvdartifacttype",
                db_index=True,
            ),
        ),
        migrations.RemoveConstraint(
            model_name="shapezgameidentifier",
            name="shapez_game_identifier_release_category_value_uniq",
        ),
        migrations.RemoveIndex(
            model_name="shapezgameidentifier",
            name="shapez_core_release_32f5d1_idx",
        ),
        migrations.AddField(
            model_name="shapezgameidentifier",
            name="identifier_category_tmp",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="identifiers_tmp",
                to="shapez_core.shapezidentifiercategory",
            ),
        ),
        migrations.RunPython(_port_identifier_categories, _noop_reverse),
        migrations.RemoveField(
            model_name="shapezgameidentifier",
            name="category",
        ),
        migrations.RenameField(
            model_name="shapezgameidentifier",
            old_name="identifier_category_tmp",
            new_name="identifier_category",
        ),
        migrations.AlterField(
            model_name="shapezgameidentifier",
            name="identifier_category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="identifiers",
                to="shapez_core.shapezidentifiercategory",
            ),
        ),
        migrations.AddConstraint(
            model_name="shapezgameidentifier",
            constraint=models.UniqueConstraint(
                fields=("release", "identifier_category", "value"),
                name="shapez_game_identifier_release_cat_value_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="shapezgameidentifier",
            index=models.Index(
                fields=["release", "identifier_category"],
                name="shapez_core_gid_release_cat_idx",
            ),
        ),
    ]
