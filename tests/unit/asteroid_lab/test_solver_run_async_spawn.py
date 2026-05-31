"""Async detach spawn + enqueue (PR-CLI-7)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    enqueue_solver_run_for_project,
)
from django_apps.asteroid_lab.services.solver_runtime_types import SolverRuntimeEntryErrorCode
from django_apps.asteroid_lab.services.solver_subprocess_runner import (
    SolverSubprocessSpawnResult,
)

pytestmark = pytest.mark.django_db


def test_enqueue_returns_active_run_conflict() -> None:
    project = m.AsteroidProject.objects.create(name="Active", slug="active-run")
    m.AsteroidMapInput.objects.create(project=project, copy_code="SHAPEZ2-4-eA==")
    m.SolverRun.objects.create(
        project=project,
        run_key="existing",
        status=m.SolverRun.RunStatus.RUNNING,
    )
    snapshot = {"schema_version": 1, "items": []}

    result = enqueue_solver_run_for_project(
        int(project.pk),
        game_data_snapshot=snapshot,
    )

    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.ACTIVE_RUN_EXISTS


@override_settings(ASTEROID_LAB_SOLVER_ASYNC_DEFAULT=True)
def test_enqueue_spawns_without_blocking(tmp_path: Path, settings) -> None:
    settings.ASTEROID_LAB_ARTIFACT_ROOT = tmp_path
    project = m.AsteroidProject.objects.create(name="Spawn", slug="spawn")
    m.AsteroidMapInput.objects.create(project=project, copy_code="SHAPEZ2-4-eA==")
    snapshot = {"schema_version": 1, "items": []}
    handle = SimpleNamespace(pid=4242)
    spawn_result = SolverSubprocessSpawnResult(
        run_key="queued-run",
        artifact_dir=tmp_path / "queued-run",
        sidecar_log_path=tmp_path / ".subprocess_logs" / "queued-run.log",
        handle=handle,
    )

    with patch(
        "django_apps.asteroid_lab.services.solver_runtime_entry.spawn_solver_subprocess_detached",
        return_value=spawn_result,
    ) as spawn_mock:
        result = enqueue_solver_run_for_project(
            int(project.pk),
            run_key="queued-run",
            game_data_snapshot=snapshot,
            status_url_builder=lambda run_id: f"/status/{run_id}/",
        )

    spawn_mock.assert_called_once()
    assert result.ok is True
    assert result.status == m.SolverRun.RunStatus.RUNNING
    assert result.status_url == f"/status/{result.solver_run_id}/"
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    assert run.status == m.SolverRun.RunStatus.RUNNING
    assert run.config_json.get("subprocess_pid") == 4242
