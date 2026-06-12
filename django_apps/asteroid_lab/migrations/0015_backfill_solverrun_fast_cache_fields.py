# Backfill denormalized SolverRun cache columns from config_json (UI-only mirrors).

from __future__ import annotations

from django.db import migrations

# Inlined from solver_run_config_keys (migrations must not import app services).
_CONFIG_LAB_REPLAY_COMPOSED_FRAMES = "lab_replay_composed_frames"
_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY = "lab_replay_manifest_summary"
_CONFIG_SOLVER_SUMMARY = "solver_summary"
_LAB_REPLAY_CACHE_SCHEMA_VERSION = 1
_LAB_REPLAY_PAYLOAD_VERSION = 1


def _dict_or_empty(raw: object) -> dict:
    return dict(raw) if isinstance(raw, dict) else {}


def _list_or_empty(raw: object) -> list:
    if not isinstance(raw, list):
        return []
    return list(raw)


def _empty_manifest_summary() -> dict[str, object]:
    return {
        "replay_payload_version": _LAB_REPLAY_PAYLOAD_VERSION,
        "lab_replay_cache_schema_version": _LAB_REPLAY_CACHE_SCHEMA_VERSION,
        "frame_count": 0,
        "preview_frame_index": 0,
        "preview_frame": None,
        "replay_track_metrics": {},
    }


def backfill_fast_cache(apps, schema_editor) -> None:  # noqa: ARG001
    SolverRun = apps.get_model("asteroid_lab", "SolverRun")
    for run in SolverRun.objects.all().iterator():
        config = dict(run.config_json or {})
        manifest_raw = config.get(_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY)
        if manifest_raw is None:
            manifest = _empty_manifest_summary()
        else:
            manifest = _dict_or_empty(manifest_raw)
        composed = _list_or_empty(config.get(_CONFIG_LAB_REPLAY_COMPOSED_FRAMES))
        metrics = _dict_or_empty(manifest.get("replay_track_metrics"))
        run.lab_replay_manifest_summary_json = manifest
        run.lab_replay_payload_json = {
            "composed_frames": composed,
            "replay_track_metrics": metrics,
        }
        run.solver_summary_json = _dict_or_empty(config.get(_CONFIG_SOLVER_SUMMARY))
        run.save(
            update_fields=[
                "lab_replay_manifest_summary_json",
                "lab_replay_payload_json",
                "solver_summary_json",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("asteroid_lab", "0014_solverrun_lab_replay_manifest_summary_json_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_fast_cache, migrations.RunPython.noop),
    ]
