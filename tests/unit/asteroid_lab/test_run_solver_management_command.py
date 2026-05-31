"""CLI ``manage.py run_solver`` when Layer 02 solver is disabled."""

from __future__ import annotations

import json
from io import StringIO

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_runtime_types import (
    SolverRuntimeEntryErrorCode,
    SolverRuntimeEntryResult,
)

pytestmark = pytest.mark.django_db


def _minimal_copy() -> str:
    return "SHAPEZ2-4-e30="


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=False)
def test_run_solver_command_subprocess_failure_raises(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proj = m.AsteroidProject.objects.create(name="CliStub", slug="cli-run-stub")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())

    monkeypatch.setattr(
        "django_apps.asteroid_lab.management.commands.run_solver.run_solver_runtime_for_project",
        lambda *args, **kwargs: SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=[],
            replay_track_metrics={"frame_count": 0},
            solver_summary={},
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.SOLVER_SUBPROCESS_FAILED,
            message="subprocess failed",
        ),
    )

    with pytest.raises(CommandError, match="subprocess failed"):
        call_command("run_solver", slug=proj.slug, stderr=StringIO())
    stderr = capsys.readouterr().err
    assert "asteroid_cli run_solver start surface=django_management slug=cli-run-stub" in stderr
    assert "asteroid_cli run_solver end surface=django_management slug=cli-run-stub" in stderr
    assert "exit=1" in stderr
    assert "ok=false" in stderr


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=False)
def test_run_solver_command_json_stdout_includes_error_code(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proj = m.AsteroidProject.objects.create(name="CliJson", slug="cli-run-json")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    monkeypatch.setattr(
        "django_apps.asteroid_lab.management.commands.run_solver.run_solver_runtime_for_project",
        lambda *args, **kwargs: SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=[],
            replay_track_metrics={"frame_count": 0},
            solver_summary={},
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.SOLVER_SUBPROCESS_FAILED,
            message="subprocess failed",
        ),
    )
    out = StringIO()
    with pytest.raises(CommandError, match="subprocess failed"):
        call_command("run_solver", slug=proj.slug, json=True, stdout=out, stderr=StringIO())
    payload = json.loads(out.getvalue())
    assert payload["error_code"] == "solver_subprocess_failed"
    stderr = capsys.readouterr().err
    assert "asteroid_cli run_solver start surface=django_management slug=cli-run-json" in stderr
    assert "asteroid_cli run_solver end surface=django_management slug=cli-run-json" in stderr


def test_run_solver_command_subprocess_flag_keeps_subprocess_only_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proj = m.AsteroidProject.objects.create(name="CliSubprocess", slug="cli-subprocess")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    calls: list[dict[str, object]] = []

    def fake_run_solver_runtime_for_project(
        project_id: int,
        **kwargs: object,
    ) -> SolverRuntimeEntryResult:
        calls.append(
            {
                "project_id": project_id,
                "solver_mode": settings.ASTEROID_LAB_SOLVER_MODE,
                "artifact_root": str(settings.ASTEROID_LAB_ARTIFACT_ROOT),
                **kwargs,
            }
        )
        return SolverRuntimeEntryResult(
            ok=True,
            solver_run_id=123,
            lab_replay_frames_json=[],
            replay_track_metrics={"frame_count": 0},
            solver_summary={"validation_passed": True},
            validation_passed=True,
        )

    monkeypatch.setattr(
        "django_apps.asteroid_lab.management.commands.run_solver.run_solver_runtime_for_project",
        fake_run_solver_runtime_for_project,
    )

    out = StringIO()
    call_command(
        "run_solver",
        slug=proj.slug,
        use_subprocess=True,
        artifact_root="F:/tmp/asteroid-cli-artifacts",
        cli_verbose=True,
        stdout=out,
        stderr=StringIO(),
    )

    assert calls
    assert calls[0]["project_id"] == int(proj.pk)
    assert calls[0]["solver_mode"] == "subprocess_only"
    assert calls[0]["artifact_root"] == "F:\\tmp\\asteroid-cli-artifacts"
    assert calls[0]["config"] == {"cli_verbose": True}
    assert "solver_run_id: 123" in out.getvalue()
