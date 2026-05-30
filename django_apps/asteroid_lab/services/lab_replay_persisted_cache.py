"""Persisted composed lab replay cache on ``SolverRun.config_json`` (13C2-lite)."""

from __future__ import annotations

import copy
from typing import Any

from django.db import transaction
from django.db.models.fields.json import KeyTransform

from django_apps.asteroid_lab.models import SolverRun
from django_apps.asteroid_lab.services.lab_replay_lazy_handle import LAB_REPLAY_PAYLOAD_VERSION
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY,
    SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY,
)

CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION = 1


def build_manifest_summary_from_compose(
    *,
    frames: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    count = len(frames)
    preview_index = max(0, count - 1) if count else 0
    preview = dict(frames[preview_index]) if count else None
    return {
        "replay_payload_version": LAB_REPLAY_PAYLOAD_VERSION,
        "lab_replay_cache_schema_version": CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION,
        "frame_count": count,
        "preview_frame_index": preview_index,
        "preview_frame": preview,
        "replay_track_metrics": dict(metrics),
    }


def is_cache_summary_valid(summary: dict[str, Any] | None) -> bool:
    if not summary or not isinstance(summary, dict):
        return False
    try:
        version = int(summary.get("lab_replay_cache_schema_version", -1))
    except (TypeError, ValueError):
        return False
    return version == CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION


def load_manifest_summary_for_run_id(run_id: int) -> dict[str, Any] | None:
    """Load manifest summary only (no ``lab_replay_composed_frames`` deserialization)."""

    key = SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY
    raw = (
        SolverRun.objects.filter(pk=int(run_id))
        .values_list(KeyTransform(key, "config_json"), flat=True)
        .first()
    )
    return dict(raw) if isinstance(raw, dict) else None


def load_composed_frames_for_run_id(run_id: int) -> list[dict[str, Any]] | None:
    """Load composed frames only via JSON key transform (not full-row ``config_json``)."""

    key = SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY
    raw = (
        SolverRun.objects.filter(pk=int(run_id))
        .values_list(KeyTransform(key, "config_json"), flat=True)
        .first()
    )
    if not isinstance(raw, list) or not raw:
        return None
    return [dict(item) for item in raw if isinstance(item, dict)]


@transaction.atomic
def persist_composed_replay_for_run_id(
    run_id: int,
    *,
    frames: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> None:
    """Fresh read-merge-write; preserve unrelated ``config_json`` keys (§4.8)."""

    summary = build_manifest_summary_from_compose(frames=frames, metrics=metrics)
    run = SolverRun.objects.select_for_update().get(pk=int(run_id))
    config = copy.deepcopy(dict(run.config_json or {}))
    config[SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY] = frames
    config[SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY] = summary
    run.config_json = config
    run.save(update_fields=["config_json"])
    from django_apps.asteroid_lab.services.solver_run_fast_cache import (
        sync_solver_run_fast_cache_from_config_json,
    )

    sync_solver_run_fast_cache_from_config_json(run)


__all__ = [
    "CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION",
    "build_manifest_summary_from_compose",
    "is_cache_summary_valid",
    "load_composed_frames_for_run_id",
    "load_manifest_summary_for_run_id",
    "persist_composed_replay_for_run_id",
]
