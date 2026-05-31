from __future__ import annotations

from django.db import migrations, models

# Columns that must satisfy SQLite JSON_VALID before ALTER TABLE table-rebuild.
_JSON_COLUMN_REPAIRS: tuple[tuple[str, str], ...] = (
    ("lab_replay_payload_json", "{}"),
    ("lab_replay_manifest_summary_json", "{}"),
    ("solver_summary_json", "{}"),
    ("config_json", "{}"),
    ("solver_runtime_replay_frames_json", "[]"),
)


def _sanitize_solverrun_json_columns(apps, schema_editor) -> None:  # noqa: ARG001
    if schema_editor.connection.vendor != "sqlite":
        return
    with schema_editor.connection.cursor() as cursor:
        for column, replacement in _JSON_COLUMN_REPAIRS:
            cursor.execute(
                f"""
                UPDATE asteroid_lab_solverrun
                SET {column} = %s
                WHERE {column} IS NOT NULL AND NOT json_valid({column})
                """,
                [replacement],
            )


class Migration(migrations.Migration):
    dependencies = [
        ("asteroid_lab", "0016_solverrun_solver_runtime_replay_frames_json"),
    ]

    operations = [
        migrations.RunPython(
            _sanitize_solverrun_json_columns,
            migrations.RunPython.noop,
        ),
        migrations.AddField(
            model_name="solverrun",
            name="artifact_root",
            field=models.CharField(
                blank=True,
                help_text="Artifact directory pointer; cache/index only, not solver input.",
                max_length=500,
            ),
        ),
        migrations.AddField(
            model_name="solverrun",
            name="lifecycle_status",
            field=models.CharField(
                blank=True,
                help_text=(
                    "DB lifecycle mirror for artifact/index state; "
                    "manifest remains artifact authority."
                ),
                max_length=40,
            ),
        ),
    ]
