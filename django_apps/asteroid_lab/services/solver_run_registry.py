"""SolverRun registry helpers for async detach + reap (PR-CLI-7)."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_subprocess_runner import (
    default_artifact_root,
    resolve_subprocess_artifact_dir,
)

TERMINAL_LIFECYCLE_STATUSES = frozenset({"indexed", "succeeded", "failed"})


class ActiveRunExistsError(Exception):
    """Raised when a project already has a RUNNING solver run."""


def subprocess_sidecar_log_path(*, artifact_root: Path, run_key: str) -> Path:
    return Path(artifact_root) / ".subprocess_logs" / f"{run_key}.log"


def planned_artifact_dir(*, artifact_root: Path, run_key: str) -> Path:
    return resolve_subprocess_artifact_dir(
        allowed_root=artifact_root,
        artifact_root=artifact_root,
        run_key=run_key,
    )


def active_running_run_for_project(project_id: int) -> m.SolverRun | None:
    return (
        m.SolverRun.objects.filter(
            project_id=int(project_id),
            status=m.SolverRun.RunStatus.RUNNING,
        )
        .order_by("-created_at", "-id")
        .first()
    )


def tail_log_text(log_path: Path, *, max_bytes: int | None = None) -> str:
    cap = int(
        max_bytes
        if max_bytes is not None
        else getattr(settings, "ASTEROID_LAB_STATUS_LOG_TAIL_BYTES", 8192)
    )
    if cap <= 0 or not log_path.is_file():
        return ""
    data = log_path.read_bytes()
    if len(data) <= cap:
        return data.decode("utf-8", errors="replace")
    return data[-cap:].decode("utf-8", errors="replace")


@transaction.atomic
def create_running_solver_run(
    *,
    project_id: int,
    run_key: str,
    spawn_config: dict[str, object],
) -> m.SolverRun:
    """Create a RUNNING row before detach spawn (one-active-run guard)."""

    if active_running_run_for_project(int(project_id)) is not None:
        raise ActiveRunExistsError(f"project {project_id} already has a running solver run")

    artifact_root = default_artifact_root()
    artifact_dir = planned_artifact_dir(artifact_root=artifact_root, run_key=run_key)
    now = timezone.now()
    run = m.SolverRun.objects.create(
        project_id=int(project_id),
        run_key=run_key,
        algorithm_label="cli_artifact",
        status=m.SolverRun.RunStatus.RUNNING,
        lifecycle_status="running",
        artifact_root=str(artifact_dir.resolve()),
        config_json=dict(spawn_config),
        started_at=now,
    )
    return run


def is_terminal_solver_run(run: m.SolverRun) -> bool:
    lifecycle = str(run.lifecycle_status or "").strip().lower()
    if lifecycle in TERMINAL_LIFECYCLE_STATUSES:
        return True
    return run.status in (
        m.SolverRun.RunStatus.COMPLETED,
        m.SolverRun.RunStatus.FAILED,
        m.SolverRun.RunStatus.CANCELLED,
        m.SolverRun.RunStatus.PARTIAL,
    )


__all__ = [
    "ActiveRunExistsError",
    "TERMINAL_LIFECYCLE_STATUSES",
    "active_running_run_for_project",
    "create_running_solver_run",
    "is_terminal_solver_run",
    "planned_artifact_dir",
    "subprocess_sidecar_log_path",
    "tail_log_text",
]
