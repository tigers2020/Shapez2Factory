"""HTTP async run-solver: 202 + status polling (PR-CLI-7)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_subprocess_runner import SolverSubprocessSpawnResult
from tests.integration.web.test_asteroid_miner_layout_solver import _unique_valid_copy
from tests.unit.asteroid_lab.test_artifact_ingest import _write_artifact

pytestmark = [pytest.mark.django_db, pytest.mark.async_solver]


@pytest.fixture
def client() -> Client:
    return Client()


@override_settings(ASTEROID_LAB_SOLVER_ASYNC_DEFAULT=True)
def test_http_run_solver_returns_202_and_status_completes(
    client: Client, tmp_path, settings
) -> None:
    settings.ASTEROID_LAB_ARTIFACT_ROOT = tmp_path
    slug = "async-http-run"
    project = m.AsteroidProject.objects.create(name="Async HTTP", slug=slug)
    m.AsteroidMapInput.objects.create(project=project, copy_code=_unique_valid_copy())

    def fake_spawn(request, **kwargs):
        del kwargs
        return SolverSubprocessSpawnResult(
            run_key=request.run_key,
            artifact_dir=tmp_path / request.run_key,
            sidecar_log_path=tmp_path / ".subprocess_logs" / f"{request.run_key}.log",
            handle=SimpleNamespace(pid=9999),
        )

    with patch(
        "django_apps.asteroid_lab.services.solver_runtime_entry.spawn_solver_subprocess_detached",
        side_effect=fake_spawn,
    ):
        with patch(
            "django_apps.web.views.public_pages.build_asteroid_game_data_snapshot_with_provenance",
            return_value=SimpleNamespace(snapshot={}, provenance={}, catalog_slice={}),
        ):
            with patch(
                "django_apps.web.views.public_pages.build_game_data_snapshot_payload",
                return_value={"schema_version": 1},
            ):
                post = client.post(
                    reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug}),
                    data={},
                    content_type="application/json",
                )

    assert post.status_code == 202
    body = post.json()
    assert body["ok"] is True
    assert body["status"] == "running"
    assert int(body["solver_run_id"]) > 0
    status_url = body["status_url"]
    assert status_url

    _write_artifact(tmp_path / body["run_key"], run_key=body["run_key"])
    status = client.get(status_url)
    assert status.status_code == 200
    status_body = status.json()
    assert status_body["status"] == m.SolverRun.RunStatus.COMPLETED
    assert status_body.get("run_summary") is not None


@override_settings(ASTEROID_LAB_SOLVER_ASYNC_DEFAULT=True)
def test_http_run_solver_returns_409_when_run_already_active(client: Client) -> None:
    slug = "async-conflict"
    project = m.AsteroidProject.objects.create(name="Conflict", slug=slug)
    m.AsteroidMapInput.objects.create(project=project, copy_code=_unique_valid_copy())
    m.SolverRun.objects.create(
        project=project, run_key="busy", status=m.SolverRun.RunStatus.RUNNING
    )

    with patch(
        "django_apps.web.views.public_pages.build_asteroid_game_data_snapshot_with_provenance",
        return_value=SimpleNamespace(snapshot={}, provenance={}, catalog_slice={}),
    ):
        with patch(
            "django_apps.web.views.public_pages.build_game_data_snapshot_payload",
            return_value={"schema_version": 1},
        ):
            post = client.post(
                reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug}),
                data={},
                content_type="application/json",
            )

    assert post.status_code == 409
    assert post.json()["error_code"] == "active_run_exists"


@override_settings(ASTEROID_LAB_SOLVER_ASYNC_DEFAULT=True)
def test_http_status_complete_does_not_warm_replay_cache(
    client: Client, tmp_path, settings
) -> None:
    settings.ASTEROID_LAB_ARTIFACT_ROOT = tmp_path
    slug = "async-no-warm"
    project = m.AsteroidProject.objects.create(name="Async No Warm", slug=slug)
    m.AsteroidMapInput.objects.create(project=project, copy_code=_unique_valid_copy())

    def fake_spawn(request, **kwargs):
        del kwargs
        return SolverSubprocessSpawnResult(
            run_key=request.run_key,
            artifact_dir=tmp_path / request.run_key,
            sidecar_log_path=tmp_path / ".subprocess_logs" / f"{request.run_key}.log",
            handle=SimpleNamespace(pid=9999),
        )

    with patch(
        "django_apps.asteroid_lab.services.solver_runtime_entry.spawn_solver_subprocess_detached",
        side_effect=fake_spawn,
    ):
        with patch(
            "django_apps.web.views.public_pages.build_asteroid_game_data_snapshot_with_provenance",
            return_value=SimpleNamespace(snapshot={}, provenance={}, catalog_slice={}),
        ):
            with patch(
                "django_apps.web.views.public_pages.build_game_data_snapshot_payload",
                return_value={"schema_version": 1},
            ):
                post = client.post(
                    reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug}),
                    data={},
                    content_type="application/json",
                )

    status_url = post.json()["status_url"]
    _write_artifact(tmp_path / post.json()["run_key"], run_key=post.json()["run_key"])

    with patch(
        "django_apps.asteroid_lab.services.artifact_ingest.build_lab_replay_frames_for_project",
    ) as compose_mock:
        status = client.get(status_url)

    compose_mock.assert_not_called()
    assert status.status_code == 200
    assert status.json()["status"] == m.SolverRun.RunStatus.COMPLETED
