"""Artifact-first reconcile for async solver runs (PR-CLI-7)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.artifact_ingest import (
    STATUS_RECONCILE_INGEST_OPTIONS,
    ArtifactIngestError,
    ingest_artifact_for_project,
)
from django_apps.asteroid_lab.services.artifact_manifest_reader import (
    ArtifactManifestReadError,
    read_verified_artifact_manifest,
)
from django_apps.asteroid_lab.services.solver_run_lab_summary import (
    lab_run_summary_from_orm,
    validation_passed_from_solver_summary,
)
from django_apps.asteroid_lab.services.solver_run_registry import (
    is_terminal_solver_run,
    subprocess_sidecar_log_path,
    tail_log_text,
)
from django_apps.asteroid_lab.services.solver_subprocess_runner import default_artifact_root

RECONCILE_FAILURE_VALIDATION = "artifact_validation_failed"
RECONCILE_FAILURE_INGEST = "artifact_ingest_failed"
RECONCILE_FAILURE_TIMEOUT = "solver_run_timeout"
RECONCILE_FAILURE_LOG_FATAL = "subprocess_log_fatal"


@dataclass(frozen=True, slots=True)
class SolverRunReconcileResult:
    """Observable solver run state after reconcile (no replay body in P0)."""

    ok: bool
    solver_run_id: int
    status: str
    lifecycle_status: str
    log_tail: str
    run_summary: dict[str, Any] | None
    validation_passed: bool
    error_code: str | None = None
    message: str | None = None


def _max_runtime_seconds() -> float:
    return float(
        getattr(
            settings,
            "ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS",
            getattr(settings, "ASTEROID_LAB_SUBPROCESS_TIMEOUT_SECONDS", 30.0),
        )
    )


def _spawn_config(run: m.SolverRun) -> dict[str, Any]:
    raw = run.config_json
    return dict(raw) if isinstance(raw, dict) else {}


def _sidecar_path_for_run(run: m.SolverRun) -> Path:
    cfg = _spawn_config(run)
    configured = cfg.get("sidecar_log_path")
    if isinstance(configured, str) and configured.strip():
        return Path(configured)
    artifact_root = default_artifact_root()
    return subprocess_sidecar_log_path(artifact_root=artifact_root, run_key=run.run_key)


def _artifact_dir_for_run(run: m.SolverRun) -> Path:
    if run.artifact_root:
        return Path(run.artifact_root).resolve()
    cfg = _spawn_config(run)
    configured = cfg.get("planned_artifact_dir")
    if isinstance(configured, str) and configured.strip():
        return Path(configured).resolve()
    return (default_artifact_root() / run.run_key).resolve()


def _log_has_fatal_marker(log_path: Path) -> bool:
    if not log_path.is_file():
        return False
    tail = tail_log_text(log_path, max_bytes=4096)
    for line in tail.splitlines():
        stripped = line.strip().lower()
        if stripped.startswith("error:") or " error: artifact " in stripped:
            return True
    return False


def _mark_run_failed_locked(
    run: m.SolverRun,
    *,
    error_code: str,
    message: str,
) -> m.SolverRun:
    run.status = m.SolverRun.RunStatus.FAILED
    run.lifecycle_status = "failed"
    run.finished_at = timezone.now()
    cfg = _spawn_config(run)
    cfg["reconcile_error_code"] = error_code
    cfg["reconcile_message"] = message
    run.config_json = cfg
    run.save(
        update_fields=[
            "status",
            "lifecycle_status",
            "finished_at",
            "config_json",
        ]
    )
    return run


def _result_from_run(run: m.SolverRun, *, log_tail: str) -> SolverRunReconcileResult:
    terminal_ok = run.status == m.SolverRun.RunStatus.COMPLETED
    summary = lab_run_summary_from_orm(run) if is_terminal_solver_run(run) else None
    cfg = _spawn_config(run)
    error_code = cfg.get("reconcile_error_code")
    message = cfg.get("reconcile_message")
    summary_json = run.solver_summary_json if isinstance(run.solver_summary_json, dict) else {}
    validation_passed = (
        validation_passed_from_solver_summary(summary_json) if summary_json else terminal_ok
    )
    return SolverRunReconcileResult(
        ok=terminal_ok,
        solver_run_id=int(run.pk),
        status=str(run.status),
        lifecycle_status=str(run.lifecycle_status or ""),
        log_tail=log_tail,
        run_summary=summary,
        validation_passed=validation_passed,
        error_code=str(error_code) if error_code else None,
        message=str(message) if message else None,
    )


def _attempt_artifact_ingest(run: m.SolverRun, artifact_dir: Path) -> tuple[bool, str | None]:
    """Ingest when manifest validates.

    Returns ``(True, None)`` if ingest completed, ``(False, None)`` if not ready,
    or ``(False, message)`` when manifest verified but ingest failed.
    """

    if not artifact_dir.is_dir() or not (artifact_dir / "manifest.json").is_file():
        return False, None
    try:
        read_verified_artifact_manifest(artifact_dir)
    except ArtifactManifestReadError:
        return False, None
    try:
        ingest_artifact_for_project(
            project_id=int(run.project_id),
            artifact_dir=artifact_dir,
            replace_existing_run=True,
            ingest_options=STATUS_RECONCILE_INGEST_OPTIONS,
        )
    except ArtifactIngestError as exc:
        return False, str(exc)
    return True, None


def reconcile_solver_run(run_id: int) -> SolverRunReconcileResult:
    """Single reconcile entry for status GET and ``run_solver_reap`` (artifact-first)."""

    artifact_dir: Path | None = None
    log_path: Path | None = None

    with transaction.atomic():
        run = m.SolverRun.objects.select_for_update().get(pk=int(run_id))
        log_path = _sidecar_path_for_run(run)
        log_tail = tail_log_text(log_path)

        if is_terminal_solver_run(run):
            return _result_from_run(run, log_tail=log_tail)

        if run.status != m.SolverRun.RunStatus.RUNNING:
            return _result_from_run(run, log_tail=log_tail)

        started = run.started_at or run.created_at
        if started is not None:
            deadline = started + timedelta(seconds=_max_runtime_seconds())
            if timezone.now() >= deadline:
                run = _mark_run_failed_locked(
                    run,
                    error_code=RECONCILE_FAILURE_TIMEOUT,
                    message="solver run exceeded max runtime",
                )
                return _result_from_run(run, log_tail=log_tail)

        artifact_dir = _artifact_dir_for_run(run)

    assert artifact_dir is not None and log_path is not None

    ingested, ingest_failure_message = _attempt_artifact_ingest(
        m.SolverRun.objects.get(pk=int(run_id)),
        artifact_dir,
    )
    if ingested:
        with transaction.atomic():
            run = m.SolverRun.objects.select_for_update().get(pk=int(run_id))
            return _result_from_run(run, log_tail=tail_log_text(log_path))

    if ingest_failure_message is not None:
        with transaction.atomic():
            run = m.SolverRun.objects.select_for_update().get(pk=int(run_id))
            if not is_terminal_solver_run(run):
                run = _mark_run_failed_locked(
                    run,
                    error_code=RECONCILE_FAILURE_INGEST,
                    message=ingest_failure_message,
                )
            return _result_from_run(run, log_tail=tail_log_text(log_path))

    if (artifact_dir / "manifest.json").is_file():
        try:
            read_verified_artifact_manifest(artifact_dir)
        except ArtifactManifestReadError as exc:
            with transaction.atomic():
                run = m.SolverRun.objects.select_for_update().get(pk=int(run_id))
                if not is_terminal_solver_run(run):
                    run = _mark_run_failed_locked(
                        run,
                        error_code=RECONCILE_FAILURE_VALIDATION,
                        message=str(exc),
                    )
                return _result_from_run(run, log_tail=tail_log_text(log_path))

    if _log_has_fatal_marker(log_path):
        with transaction.atomic():
            run = m.SolverRun.objects.select_for_update().get(pk=int(run_id))
            if not is_terminal_solver_run(run):
                run = _mark_run_failed_locked(
                    run,
                    error_code=RECONCILE_FAILURE_LOG_FATAL,
                    message="subprocess log contains fatal error marker",
                )
            return _result_from_run(run, log_tail=tail_log_text(log_path))

    with transaction.atomic():
        run = m.SolverRun.objects.select_for_update().get(pk=int(run_id))
        return _result_from_run(run, log_tail=tail_log_text(log_path))


def reconcile_running_solver_runs() -> list[SolverRunReconcileResult]:
    """Batch reap: every RUNNING row through ``reconcile_solver_run``."""

    results: list[SolverRunReconcileResult] = []
    run_ids = list(
        m.SolverRun.objects.filter(status=m.SolverRun.RunStatus.RUNNING)
        .order_by("id")
        .values_list("pk", flat=True)
    )
    for run_id in run_ids:
        results.append(reconcile_solver_run(int(run_id)))
    return results


__all__ = [
    "RECONCILE_FAILURE_INGEST",
    "RECONCILE_FAILURE_LOG_FATAL",
    "RECONCILE_FAILURE_TIMEOUT",
    "RECONCILE_FAILURE_VALIDATION",
    "SolverRunReconcileResult",
    "reconcile_running_solver_runs",
    "reconcile_solver_run",
]
