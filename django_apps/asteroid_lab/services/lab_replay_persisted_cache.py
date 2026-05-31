"""Artifact-first lab replay cache readers for ``SolverRun`` UI/index fields."""

from __future__ import annotations

import copy
from typing import Any

from django.db import transaction
from django.db.models.fields.json import KeyTransform

from django_apps.asteroid_lab.models import SolverRun
from django_apps.asteroid_lab.services.artifact_replay_viewer_compose import (
    lab_replay_frames_are_renderable,
)
from django_apps.asteroid_lab.services.lab_replay_lazy_handle import (
    LAB_REPLAY_PAYLOAD_VERSION,
    preview_frame_index_for_lab_replay,
)
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
    preview_index = preview_frame_index_for_lab_replay(frames)
    preview = dict(frames[preview_index]) if count else None
    return {
        "replay_payload_version": LAB_REPLAY_PAYLOAD_VERSION,
        "lab_replay_cache_schema_version": CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION,
        "frame_count": count,
        "preview_frame_index": preview_index,
        "preview_frame": preview,
        "replay_track_metrics": dict(metrics),
    }


def is_artifact_replay_source_summary(summary: dict[str, Any] | None) -> bool:
    """True when ``replay_core.jsonl`` is indexed (compose source, not display cache)."""

    if not summary or not isinstance(summary, dict):
        return False
    if summary.get("mode") == "artifact_jsonl":
        return isinstance(summary.get("replay_core_path"), str) and bool(
            summary.get("replay_core_path")
        )
    return False


def _artifact_replay_source_snapshot(summary: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return artifact index summary to preserve across composed-cache writes."""

    if not summary or not isinstance(summary, dict):
        return None
    if is_artifact_replay_source_summary(summary):
        return dict(summary)
    nested = summary.get("artifact_replay_source")
    if isinstance(nested, dict) and is_artifact_replay_source_summary(nested):
        return dict(nested)
    return None


def is_cache_summary_valid(summary: dict[str, Any] | None) -> bool:
    if not summary or not isinstance(summary, dict):
        return False
    if is_artifact_replay_source_summary(summary):
        return True
    try:
        version = int(summary.get("lab_replay_cache_schema_version", -1))
    except (TypeError, ValueError):
        return False
    return version == CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION


def _dict_or_none(raw: Any) -> dict[str, Any] | None:
    return dict(raw) if isinstance(raw, dict) else None


def load_manifest_summary_for_run_id(run_id: int) -> dict[str, Any] | None:
    """Load manifest summary from artifact/index fields before legacy config fallback."""

    direct = (
        SolverRun.objects.filter(pk=int(run_id))
        .values_list("lab_replay_manifest_summary_json", flat=True)
        .first()
    )
    summary = _dict_or_none(direct)
    if summary:
        return summary

    key = SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY
    raw = (
        SolverRun.objects.filter(pk=int(run_id))
        .values_list(KeyTransform(key, "config_json"), flat=True)
        .first()
    )
    return _dict_or_none(raw)


def load_composed_frames_for_run_id(run_id: int) -> list[dict[str, Any]] | None:
    """Load replay frames artifact-first, then dedicated DB cache, then legacy config."""

    row = (
        SolverRun.objects.filter(pk=int(run_id))
        .values(
            "lab_replay_manifest_summary_json",
            "lab_replay_payload_json",
        )
        .first()
    )
    if row is not None:
        payload = _dict_or_none(row.get("lab_replay_payload_json"))
        if payload:
            composed = payload.get("composed_frames")
            if isinstance(composed, list) and composed:
                frames = [dict(item) for item in composed if isinstance(item, dict)]
                if lab_replay_frames_are_renderable(frames):
                    return frames

    key = SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY
    raw = (
        SolverRun.objects.filter(pk=int(run_id))
        .values_list(KeyTransform(key, "config_json"), flat=True)
        .first()
    )
    if not isinstance(raw, list) or not raw:
        return None
    frames = [dict(item) for item in raw if isinstance(item, dict)]
    if not frames:
        return None
    summary = _dict_or_none(
        SolverRun.objects.filter(pk=int(run_id))
        .values_list("lab_replay_manifest_summary_json", flat=True)
        .first()
    )
    if is_artifact_replay_source_summary(summary):
        return frames if lab_replay_frames_are_renderable(frames) else None
    if is_cache_summary_valid(summary):
        return frames
    return frames if lab_replay_frames_are_renderable(frames) else None


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
    artifact_source = _artifact_replay_source_snapshot(
        _dict_or_none(run.lab_replay_manifest_summary_json),
    )
    if artifact_source is not None:
        summary = {
            **summary,
            "mode": artifact_source.get("mode"),
            "replay_core_path": artifact_source.get("replay_core_path", ""),
            "artifact_run_key": artifact_source.get("artifact_run_key"),
            "artifact_replay_source": artifact_source,
        }
    config = copy.deepcopy(dict(run.config_json or {}))
    config[SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY] = frames
    config[SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY] = summary
    run.config_json = config
    run.lab_replay_payload_json = {"composed_frames": frames}
    run.lab_replay_manifest_summary_json = summary
    run.save(
        update_fields=[
            "config_json",
            "lab_replay_payload_json",
            "lab_replay_manifest_summary_json",
        ]
    )
    from django_apps.asteroid_lab.services.solver_run_fast_cache import (
        sync_solver_run_fast_cache_from_config_json,
    )

    sync_solver_run_fast_cache_from_config_json(run)


__all__ = [
    "CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION",
    "build_manifest_summary_from_compose",
    "is_artifact_replay_source_summary",
    "is_cache_summary_valid",
    "load_composed_frames_for_run_id",
    "load_manifest_summary_for_run_id",
    "persist_composed_replay_for_run_id",
]
