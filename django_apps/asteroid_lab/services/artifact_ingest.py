"""Ingest finalized CLI artifacts into Django index/cache rows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from django.db import transaction
from django.utils import timezone

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.artifact_manifest_reader import (
    ArtifactManifestReadError,
    ArtifactManifestRecord,
    read_verified_artifact_manifest,
)
from django_apps.asteroid_lab.services.artifact_replay_loader import iter_replay_core_frames
from django_apps.asteroid_lab.services.artifact_replay_viewer_compose import (
    lab_replay_frames_are_renderable,
)
from django_apps.asteroid_lab.services.lab_replay_lazy_handle import LAB_REPLAY_PAYLOAD_VERSION
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import (
    CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION,
    persist_composed_replay_for_run_id,
    replay_compose_cache_enabled,
)
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)


class ArtifactIngestError(Exception):
    """Raised when artifact ingest must fail closed."""


@dataclass(frozen=True, slots=True)
class ArtifactIngestResult:
    """SolverRun row and manifest indexed from a finalized artifact."""

    solver_run: m.SolverRun
    manifest: ArtifactManifestRecord
    solver_summary: dict[str, object]


@dataclass(frozen=True, slots=True)
class ArtifactIngestOptions:
    """Per-caller ingest behavior. Status reconcile uses the fast path."""

    warm_replay_cache: bool = True
    summarize_replay_frames: bool = True


STATUS_RECONCILE_INGEST_OPTIONS = ArtifactIngestOptions(
    warm_replay_cache=False,
    summarize_replay_frames=False,
)


def _dict_json_file(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactIngestError(f"invalid JSON payload: {path}") from exc
    if not isinstance(payload, dict):
        raise ArtifactIngestError(f"JSON payload must be an object: {path}")
    return dict(payload)


def _manifest_path(artifact_dir: Path, manifest: ArtifactManifestRecord, key: str) -> Path | None:
    relpath = manifest.paths.get(key)
    if not relpath:
        return None
    root = Path(artifact_dir).resolve()
    path = (root / str(relpath)).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ArtifactIngestError(f"manifest path escapes artifact: {key}") from exc
    return path


def _lab_replay_manifest_summary(
    *,
    artifact_dir: Path,
    manifest: ArtifactManifestRecord,
    summarize_replay_frames: bool = True,
) -> dict[str, object]:
    replay_path = _manifest_path(artifact_dir, manifest, "replay_core")
    frame_count = 0
    preview_frame_index = 0
    if summarize_replay_frames and replay_path is not None and replay_path.is_file():
        for _frame in iter_replay_core_frames(replay_path):
            frame_count += 1
        if frame_count:
            preview_frame_index = frame_count - 1
    return {
        "mode": "artifact_jsonl",
        "replay_payload_version": LAB_REPLAY_PAYLOAD_VERSION,
        "lab_replay_cache_schema_version": CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION,
        "artifact_run_key": manifest.run_key,
        "replay_core_path": str(replay_path) if replay_path is not None else "",
        "frame_count": frame_count,
        "preview_frame_index": preview_frame_index,
        # Raw replay_core lines lack map_view; viewer compose supplies renderable preview.
        "preview_frame": None,
        "replay_track_metrics": {},
    }


def _warm_lab_replay_cache_after_artifact_ingest(*, project_id: int, run_id: int) -> None:
    """Compose artifact replay for lazy SSR preview (non-fatal on failure)."""

    if not replay_compose_cache_enabled():
        return

    try:
        frames, metrics = build_lab_replay_frames_for_project(
            int(project_id),
            solver_run_id=int(run_id),
        )
    except Exception:
        return
    if not lab_replay_frames_are_renderable(frames):
        return
    persist_composed_replay_for_run_id(int(run_id), frames=frames, metrics=metrics)


def ingest_artifact_for_project(
    *,
    project_id: int,
    artifact_dir: Path,
    replace_existing_run: bool = False,
    ingest_options: ArtifactIngestOptions | None = None,
) -> ArtifactIngestResult:
    """Verify a finalized artifact and write index/cache fields only."""

    options = ingest_options or ArtifactIngestOptions()

    try:
        manifest = read_verified_artifact_manifest(Path(artifact_dir))
    except ArtifactManifestReadError as exc:
        raise ArtifactIngestError(str(exc)) from exc

    summary_path = _manifest_path(Path(artifact_dir), manifest, "solver_summary")
    solver_summary = _dict_json_file(summary_path) if summary_path is not None else {}
    config_json = {
        "artifact_dir": str(Path(artifact_dir).resolve()),
        "artifact_manifest": {
            "schema_version": manifest.schema_version,
            "run_key": manifest.run_key,
            "lifecycle_status": manifest.lifecycle_status,
            "created_at_utc": manifest.created_at_utc,
            "core_build_id": manifest.core_build_id,
            "paths": dict(manifest.paths),
            "content_hashes": dict(manifest.content_hashes),
            "game_data_provenance": dict(manifest.game_data_provenance),
            "error_code": manifest.error_code,
        },
        SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY: dict(solver_summary),
    }
    artifact_root = str(Path(artifact_dir).resolve())
    status = (
        m.SolverRun.RunStatus.FAILED if manifest.error_code else m.SolverRun.RunStatus.COMPLETED
    )

    with transaction.atomic():
        existing = m.SolverRun.objects.filter(
            project_id=int(project_id),
            run_key=manifest.run_key,
        ).first()
        if existing is not None and not replace_existing_run:
            raise ArtifactIngestError(f"solver run already exists: {manifest.run_key}")
        run = existing or m.SolverRun(project_id=int(project_id), run_key=manifest.run_key)
        run.algorithm_label = "cli_artifact"
        run.status = status
        run.artifact_root = artifact_root
        run.lifecycle_status = (
            "succeeded" if status == m.SolverRun.RunStatus.COMPLETED else "failed"
        )
        run.config_json = config_json
        run.solver_summary_json = solver_summary
        run.lab_replay_manifest_summary_json = _lab_replay_manifest_summary(
            artifact_dir=Path(artifact_dir),
            manifest=manifest,
            summarize_replay_frames=options.summarize_replay_frames,
        )
        run.lab_replay_payload_json = {}
        run.solver_runtime_replay_frames_json = []
        run.finished_at = timezone.now()
        run.save()
        run_id = int(run.pk)

    if status == m.SolverRun.RunStatus.COMPLETED and options.warm_replay_cache:
        _warm_lab_replay_cache_after_artifact_ingest(
            project_id=int(project_id),
            run_id=run_id,
        )

    return ArtifactIngestResult(
        solver_run=run,
        manifest=manifest,
        solver_summary=solver_summary,
    )


__all__ = [
    "ArtifactIngestError",
    "ArtifactIngestOptions",
    "ArtifactIngestResult",
    "STATUS_RECONCILE_INGEST_OPTIONS",
    "ingest_artifact_for_project",
]
