"""Management command run_solver_reap."""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_run_registry import create_running_solver_run
from tests.unit.asteroid_lab.test_artifact_ingest import _write_artifact

pytestmark = pytest.mark.django_db


def test_run_solver_reap_command_ingests_ready_runs(tmp_path, settings) -> None:
    settings.ASTEROID_LAB_ARTIFACT_ROOT = tmp_path
    project = m.AsteroidProject.objects.create(name="Cmd", slug="cmd-reap")
    run = create_running_solver_run(
        project_id=int(project.pk),
        run_key="cmd-run",
        spawn_config={"planned_artifact_dir": str((tmp_path / "cmd-run").resolve())},
    )
    _write_artifact(tmp_path / "cmd-run", run_key="cmd-run")

    out = StringIO()
    call_command("run_solver_reap", stdout=out)

    refreshed = m.SolverRun.objects.get(pk=int(run.pk))
    assert refreshed.status == m.SolverRun.RunStatus.COMPLETED
    assert "run_id=" in out.getvalue()
