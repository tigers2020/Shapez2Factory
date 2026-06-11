"""HTTP run-solver console trace wiring."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from django.test import RequestFactory, override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_runtime_types import SolverRuntimeEntryResult
from django_apps.web.views import public_pages

pytestmark = pytest.mark.django_db


@override_settings(ASTEROID_LAB_SOLVER_ASYNC_DEFAULT=False)
def test_http_run_solver_emits_cli_trace(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = m.AsteroidProject.objects.create(name="Trace Project", slug="trace-project")
    request = RequestFactory().post("/run-solver/", data={}, content_type="application/json")

    monkeypatch.setattr(
        public_pages,
        "build_asteroid_game_data_snapshot_with_provenance",
        lambda: SimpleNamespace(snapshot={}, provenance={}, catalog_slice={}),
    )
    monkeypatch.setattr(
        public_pages,
        "build_game_data_snapshot_payload",
        lambda: {"schema_version": 1},
    )
    monkeypatch.setattr(
        public_pages,
        "run_solver_runtime_for_project",
        lambda *_args, **_kwargs: SolverRuntimeEntryResult(
            ok=True,
            solver_run_id=None,
            lab_replay_frames_json=[],
            replay_track_metrics={},
            solver_summary={},
            validation_passed=True,
        ),
    )

    response = public_pages._run_solver_post_traced(
        request,
        slug=project.slug,
        project=project,
        run_config={},
    )

    assert response.status_code == 200
    assert json.loads(response.content.decode())["ok"] is True
    stderr = capsys.readouterr().err
    assert "asteroid_cli run_solver start surface=http_run_solver slug=trace-project" in stderr
    assert "asteroid_cli run_solver end surface=http_run_solver slug=trace-project" in stderr
    assert "exit=0" in stderr
    assert "ok=true" in stderr
