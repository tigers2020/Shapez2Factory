"""ORM fast-cache mirrors on ``SolverRun`` (UI/index only; never solver algorithm input)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.models import SolverRun
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import (
    CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION,
)
from django_apps.asteroid_lab.services.lab_replay_lazy_handle import LAB_REPLAY_PAYLOAD_VERSION
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY,
    SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY,
    SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)

# Uses ``lab_replay_persisted_cache.CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION`` via import.

_FAST_CACHE_UPDATE_FIELDS = (
    "lab_replay_manifest_summary_json",
    "lab_replay_payload_json",
    "solver_summary_json",
    "solver_runtime_replay_frames_json",
)


def empty_lab_replay_manifest_summary() -> dict[str, Any]:
    return {
        "replay_payload_version": LAB_REPLAY_PAYLOAD_VERSION,
        "lab_replay_cache_schema_version": CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION,
        "frame_count": 0,
        "preview_frame_index": 0,
        "preview_frame": None,
        "replay_track_metrics": {},
    }


def empty_solver_run_fast_cache_kwargs() -> dict[str, Any]:
    """Keyword args for ``SolverRun.objects.create`` / ``create_solver_run``."""

    return {
        "lab_replay_manifest_summary_json": empty_lab_replay_manifest_summary(),
        "lab_replay_payload_json": {},
        "solver_summary_json": {},
        "solver_runtime_replay_frames_json": [],
    }


def _dict_or_empty(raw: Any) -> dict[str, Any]:
    return dict(raw) if isinstance(raw, dict) else {}


def _list_or_empty(raw: Any) -> list[Any]:
    if not isinstance(raw, list):
        return []
    return list(raw)


def sync_solver_run_fast_cache_from_config_json(run: SolverRun) -> None:
    """Mirror selected ``config_json`` keys onto denormalized JSON columns."""

    config = dict(run.config_json or {})
    manifest_raw = config.get(SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY)
    if manifest_raw is None:
        manifest = empty_lab_replay_manifest_summary()
    else:
        manifest = _dict_or_empty(manifest_raw)
    composed = _list_or_empty(config.get(SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY))
    metrics = _dict_or_empty(manifest.get("replay_track_metrics"))
    run.lab_replay_manifest_summary_json = manifest
    run.lab_replay_payload_json = {
        "composed_frames": composed,
        "replay_track_metrics": metrics,
    }
    summary_from_config = _dict_or_empty(config.get(SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY))
    column_summary = _dict_or_empty(run.solver_summary_json)
    if summary_from_config:
        run.solver_summary_json = summary_from_config
    elif column_summary:
        run.solver_summary_json = column_summary
    else:
        run.solver_summary_json = {}
    run.solver_runtime_replay_frames_json = _list_or_empty(
        config.get(SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY)
    )
    run.save(update_fields=list(_FAST_CACHE_UPDATE_FIELDS))


__all__ = [
    "empty_lab_replay_manifest_summary",
    "empty_solver_run_fast_cache_kwargs",
    "sync_solver_run_fast_cache_from_config_json",
]
